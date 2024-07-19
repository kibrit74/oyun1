import os
import re
from flask import Flask, render_template, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
from gtts import gTTS
from groq import Groq

app = Flask(__name__)

# Groq API anahtarınızı buraya ekleyin
client = Groq(api_key="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")

def extract_video_id(url):
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
    prompt = f"""
    Translate the following text to Turkish. 
    The translation should adhere to the following guidelines:
    1. The translation should be fluent and natural-sounding in Turkish.
    2. The translation should be easy to understand.
    3. Preserve the original meaning accurately.
    4. Adapt idioms and expressions to Turkish equivalents where appropriate.
    5. Maintain the tone and style of the original text.

    Here is the text to translate:

    {text}
    """
    
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a highly skilled multilingual translator specializing in translations to Turkish. Your goal is to produce fluent, natural-sounding, and easily understandable Turkish translations from any source language. Please follow the provided guidelines strictly."
            },
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="gemma2-9b-it",
    )
    return chat_completion.choices[0].message.content


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
    audio_file_path = os.path.join('static', 'audio', output_file).replace("\\", "/")

    if os.path.exists(audio_file_path):
        print(f"Ses dosyası zaten mevcut: {audio_file_path}")
        audio_file_url = f"audio/{output_file}"
        return jsonify({'audio_file': audio_file_url, 'video_id': video_id})
    
    transcript = get_youtube_transcript(video_id)
    
    if transcript:
        translated_text = translate_text(transcript)
        audio_file_path = text_to_speech(translated_text, output_file).replace("\\", "/")
        audio_file_url = f"audio/{output_file}"
        return jsonify({'audio_file': audio_file_url, 'video_id': video_id})
    else:
        return jsonify({'error': 'Transkript alınamadı'}), 500

if __name__ == "__main__":
    app.run(debug=True)