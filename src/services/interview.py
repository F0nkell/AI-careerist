import os
import base64
import uuid
import asyncio
from pathlib import Path
from fastapi import UploadFile
from openai import AsyncOpenAI # OpenRouter совместим с OpenAI клиентом
import speech_recognition as sr
from pydub import AudioSegment
from gtts import gTTS

from src.config import settings

# --- ГЛАВНОЕ ИЗМЕНЕНИЕ ЗДЕСЬ ---
client = AsyncOpenAI(
    api_key=settings.OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1" # Адрес OpenRouter
)
# -------------------------------

TEMP_DIR = Path("temp_audio")
TEMP_DIR.mkdir(exist_ok=True)

async def process_voice_interview(file: UploadFile) -> dict:
    unique_id = uuid.uuid4().hex
    input_path = TEMP_DIR / f"{unique_id}_raw"
    wav_path = TEMP_DIR / f"{unique_id}.wav"
    output_path = TEMP_DIR / f"{unique_id}_output.mp3"

    try:
        # 1. Сохраняем
        content = await file.read()
        with open(input_path, "wb") as f:
            f.write(content)

        # 2. Конвертируем в WAV (для распознавания)
        sound = AudioSegment.from_file(input_path)
        sound.export(wav_path, format="wav")

        # 3. Распознаем речь (Бесплатно через Google)
        r = sr.Recognizer()
        with sr.AudioFile(str(wav_path)) as source:
            audio_data = r.record(source)
            try:
                user_text = await asyncio.to_thread(r.recognize_google, audio_data, language="ru-RU")
            except sr.UnknownValueError:
                user_text = "..."
            except sr.RequestError:
                user_text = "(Ошибка распознавания)"

        print(f"DEBUG: User said: {user_text}")

        # 4. Отправляем в OpenRouter
        # Используем бесплатную модель (или дешевую)
        # Варианты: "deepseek/deepseek-chat", "google/gemini-2.0-flash-exp:free"
        response = await client.chat.completions.create(
            model="deepseek/deepseek-chat", # <-- Формат имени модели в OpenRouter
            messages=[
                {"role": "system", "content": "Ты строгий HR. Отвечай на русском, кратко (1 предложение)."},
                {"role": "user", "content": user_text},
            ],
            # Дополнительные заголовки, которые просит OpenRouter (для статистики)
            extra_headers={
                "HTTP-Referer": "https://t.me/YourBot", 
                "X-Title": "ResumeKillerApp",
            }
        )
        ai_text = response.choices[0].message.content
        print(f"DEBUG: AI said: {ai_text}")

        # 5. Озвучка (TTS)
        def save_tts():
            tts = gTTS(text=ai_text, lang='ru')
            tts.save(str(output_path))
        
        await asyncio.to_thread(save_tts)

        # 6. Base64
        with open(output_path, "rb") as audio_file:
            audio_base64 = base64.b64encode(audio_file.read()).decode('utf-8')

        return {
            "user_text": user_text,
            "ai_text": ai_text,
            "audio_base64": audio_base64
        }

    except Exception as e:
        print(f"OpenRouter Error: {e}")
        # Возвращаем ошибку текстом, чтобы видеть в Swagger
        return {
            "user_text": "Ошибка",
            "ai_text": f"API Error: {str(e)}",
            "audio_base64": ""
        }

    finally:
        for p in [input_path, wav_path, output_path]:
            if p.exists():
                try: os.remove(p)
                except: pass