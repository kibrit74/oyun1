import os
import re
from flask import Flask, render_template, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
from gtts import gTTS

app = Flask(__name__)

# Google Gemini API anahtarınızı buraya ekleyin
genai.configure(api_key="AIzaSyBWC2gp-UjhlnGQgM0S77lftXnSl0uhqQ0")

def extract_video_id(url):
    # YouTube linkinden video ID'sini çıkaran fonksiyon
    pattern = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com|youtu\.be)\/(?:watch\?v=)?(.{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None

def get_youtube_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return ' '.join([entry['text'] for entry in transcript])
    except Exception as e:
        print(f"Transkript alınamadı: {e}")
        return None

def translate_text(text):
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"Translate the following text to Turkish: {text}"
    response = model.generate_content(prompt)
    return response.text

def text_to_speech(text, output_file):
    tts = gTTS(text=text, lang='tr')
    output_dir = os.path.join('static', 'audio')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    file_path = os.path.join(output_dir, output_file)
    tts.save(file_path)
    print(f"Ses dosyası {file_path} olarak kaydedildi.")
    return file_path

@app.route('/')
def index():
    return render_template('index111.html')

@app.route('/play')
def play():
    video_url = request.args.get('video_url')
    video_id = extract_video_id(video_url)
    if video_id:
        return render_template('play.html', video_id=video_id)
    else:
        return "Geçersiz YouTube URL'si", 400

@app.route('/translate', methods=['POST'])
def translate():
    video_url = request.form['video_url']
    video_id = extract_video_id(video_url)
    
    if not video_id:
        return jsonify({'error': 'Geçersiz YouTube URL\'si'}), 400
    
    output_file = f"{video_id}_tr.mp3"
    audio_file_path = os.path.join('static', 'audio', output_file).replace("\\", "/")  # Windows yollarını düzelt
    
    if os.path.exists(audio_file_path):
        print(f"Ses dosyası zaten mevcut: {audio_file_path}")
        # Return the correct URL for the existing file
        audio_file_url = f"audio/{output_file}"
        return jsonify({'audio_file': audio_file_url, 'video_id': video_id})
    
    transcript = get_youtube_transcript(video_id)
    
    if transcript:
        translated_text = translate_text(transcript)
        audio_file_path = text_to_speech(translated_text, output_file).replace("\\", "/")
        # Return the correct URL for the new file
        audio_file_url = f"audio/{output_file}"
        return jsonify({'audio_file': audio_file_url, 'video_id': video_id})
    else:
        return jsonify({'error': 'Transkript alınamadı'}), 500

if __name__ == "__main__":
    app.run(debug=True)
