import google.generativeai as genai
from flask import Flask, request, jsonify, render_template, send_file
import speech_recognition as sr
import wave
from gtts import gTTS
import io
import json
import tempfile
import os
import logging

# Logging'i yapılandır
logging.basicConfig(level=logging.DEBUG)

genai.configure(api_key="AIzaSyBWC2gp-UjhlnGQgM0S77lftXnSl0uhqQ0")
model = genai.GenerativeModel('gemini-pro')

app = Flask(__name__)

duas = {
    "fatiha": "Bismillahirrahmanirrahim. Elhamdülillahi rabbil alemin. Errahmanir rahim. Maliki yevmiddin. İyyake na'budü ve iyyake nestain. İhdinas sıratal müstakim. Sıratallezine en'amte aleyhim ğayril mağdubi aleyhim ve led dallin.",
    "ayetel_kursi": "Allahü la ilahe illa hüvel hayyül kayyum. La te'huzühu sinetün ve la nevm. Lehu ma fis semavati ve ma fil ard. Men zellezi yeşfeu indehu illa bi iznih. Ya'lemu ma beyne eydihim ve ma halfehüm ve la yuhitune bi şey'in min ilmihi illa bi ma şa'. Vesia kürsiyyühüs semavati vel ard. Ve la yeudühu hifzuhüma ve hüvel aliyyül azim."
}

def model_based_pronunciation_and_explanation(text):
    response = model.generate_content(f"""
    Lütfen aşağıdaki duayı önce Arapça telaffuzuna en yakın şekilde Latin alfabesi kullanarak yaz, 
    ardından Türkçe açıklamasını ve anlamını ver.
    
    Yanıtı şu formatta oluştur:
    Arapça Telaffuz: [duanın Arapça telaffuzu]
    Türkçe Açıklama: [duanın Türkçe açıklaması ve anlamı]
    
    Dua: "{text}"
    """)
    return response.text.strip()

def text_to_speech(text, lang='ar'):
    try:
        pronunciation = model_based_pronunciation_and_explanation(text)
        arabic_part = pronunciation.split("Türkçe Açıklama:")[0].replace("Arapça Telaffuz:", "").strip()
        tts = gTTS(text=arabic_part, lang=lang)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp, pronunciation
    except Exception as e:
        logging.error(f"Error in text_to_speech: {str(e)}")
        return None, str(e)

def speech_to_text(audio_file_path):
    recognizer = sr.Recognizer()
    try:
        # WAV dosyasını açın ve parametreleri alın
        with wave.open(audio_file_path, 'rb') as wf:
            sample_width = wf.getsampwidth()
            rate = wf.getframerate()
            channels = wf.getnchannels()
            frames = wf.readframes(wf.getnframes())

        # SpeechRecognition için bir AudioData nesnesi oluşturun
        audio_data = sr.AudioData(frames, rate, sample_width)
        
        # Ses tanıma işlemini gerçekleştirin
        text = recognizer.recognize_google(audio_data, language="tr-TR")
        return text
    except sr.UnknownValueError:
        return "Ses anlaşılamadı"
    except sr.RequestError as e:
        logging.error(f"RequestError in speech_to_text: {str(e)}")
        return "Ses tanıma servisi çalışmıyor"
    except Exception as e:
        logging.error(f"Unexpected error in speech_to_text: {str(e)}")
        return f"Beklenmeyen bir hata oluştu: {str(e)}"


@app.route('/')
def dua():
    return render_template('dua.html', duas=json.dumps(list(duas.keys())))

@app.route('/get_dua', methods=['POST'])
def get_dua():
    dua_name = request.json['dua_name']
    if dua_name in duas:
        audio_fp, pronunciation = text_to_speech(duas[dua_name])
        if audio_fp is None:
            return jsonify({"error": pronunciation}), 500
        return jsonify({
            "dua_text": duas[dua_name],
            "pronunciation": pronunciation
        })
    else:
        return jsonify({"error": "Dua bulunamadı"}), 404

@app.route('/get_audio', methods=['POST'])
def get_audio():
    text = request.json['text']
    audio_fp, error = text_to_speech(text)
    if audio_fp is None:
        return jsonify({"error": error}), 500
    return send_file(audio_fp, mimetype="audio/mp3")

@app.route('/analyze', methods=['POST'])
def analyze_pronunciation():
    if 'audio' not in request.files:
        return jsonify({"error": "Ses dosyası bulunamadı"}), 400
    
    audio_file = request.files['audio']
    original_text = request.form['text']
    
    try:
        # Geçici bir dosya oluştur ve ses verilerini kaydet
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
            audio_file.save(temp_audio.name)
            temp_audio_path = temp_audio.name

        # Geçici dosyayı kullanarak speech_to_text işlemini gerçekleştir
        recognized_text = speech_to_text(temp_audio_path)
        
        # Geçici dosyayı sil
        os.unlink(temp_audio_path)
        
        # Eğer speech_to_text bir hata mesajı döndürdüyse, bunu kullanıcıya ilet
        if recognized_text.startswith("Speech recognition kütüphanesi ile ilgili bir hata oluştu") or \
           recognized_text.startswith("Ses tanıma servisi çalışmıyor") or \
           recognized_text.startswith("Beklenmeyen bir hata oluştu"):
            return jsonify({"error": recognized_text}), 500

        response = model.generate_content(f"""
        Orijinal dua metni: {original_text}
        Kullanıcının okuduğu metin: {recognized_text}
        
        Yukarıdaki iki metin arasındaki telaffuz farklılıklarını analiz et.
        Yanıtı Türkçe olarak şu formatta ver:
        Doğru okunan kısımlar: [doğru okunan kelime veya cümleler]
        Hatalı okunan kısımlar: [hatalı okunan kelime veya cümleler ve nasıl düzeltilmesi gerektiği]
        Genel öneriler: [telaffuzu geliştirmek için genel tavsiyeler]
        """)
        
        result = response.text.split("Hatalı okunan kısımlar:")
        correct_parts = result[0].replace("Doğru okunan kısımlar:", "").strip()
        errors_and_suggestions = result[1].split("Genel öneriler:")
        errors = errors_and_suggestions[0].strip()
        suggestions = errors_and_suggestions[1].strip() if len(errors_and_suggestions) > 1 else ""
        
        return jsonify({
            "recognized_text": recognized_text,
            "correct_parts": correct_parts,
            "errors": errors,
            "suggestions": suggestions
        })
    except Exception as e:
        logging.error(f"Error in analyze_pronunciation: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)