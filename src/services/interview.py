import os
import base64
import uuid
import asyncio
from pathlib import Path
from fastapi import UploadFile
from groq import AsyncGroq  # Клиент Groq
from gtts import gTTS       # Бесплатный TTS от Google

from src.config import settings

# Инициализация Groq
client = AsyncGroq(api_key=settings.GROQ_API_KEY)

TEMP_DIR = Path("temp_audio")
TEMP_DIR.mkdir(exist_ok=True)

async def process_voice_interview(file: UploadFile) -> dict:
    unique_id = uuid.uuid4().hex
    input_path = TEMP_DIR / f"{unique_id}_input.m4a" # Groq любит m4a/mp3
    output_path = TEMP_DIR / f"{unique_id}_output.mp3"

    try:
        # 1. Сохраняем файл от юзера
        content = await file.read()
        with open(input_path, "wb") as f:
            f.write(content)

        # 2. STT (Слух) через Groq (Whisper)
        with open(input_path, "rb") as audio_file:
            transcription = await client.audio.transcriptions.create(
                file=(input_path.name, audio_file.read()),
                model="whisper-large-v3", # Мощная бесплатная модель
                response_format="json",
                language="ru",
                temperature=0.0
            )
        user_text = transcription.text

        # 3. LLM (Мозг) через Groq (Llama 3 или Mixtral)
        chat_completion = await client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Ты строгий HR. Говори кратко, на русском языке. Задавай по одному вопросу."
                },
                {
                    "role": "user",
                    "content": user_text,
                }
            ],
            model="llama3-8b-8192", # Очень быстрая и умная модель
        )
        ai_text = chat_completion.choices[0].message.content

        # 4. TTS (Голос) через gTTS (Google)
        # gTTS синхронная, поэтому запускаем её в отдельном потоке, чтобы не блокировать сервер
        def save_tts():
            tts = gTTS(text=ai_text, lang='ru')
            tts.save(str(output_path))
        
        await asyncio.to_thread(save_tts)

        # 5. Кодируем в Base64
        with open(output_path, "rb") as audio_file:
            audio_base64 = base64.b64encode(audio_file.read()).decode('utf-8')

        return {
            "user_text": user_text,
            "ai_text": ai_text,
            "audio_base64": audio_base64
        }

    except Exception as e:
        print(f"Error: {e}")
        # Возвращаем заглушку при ошибке, чтобы фронт не падал
        return {
            "user_text": "Ошибка обработки",
            "ai_text": f"Произошла ошибка на сервере: {str(e)}",
            "audio_base64": ""
        }

    finally:
        # Чистим файлы
        if input_path.exists():
            try: os.remove(input_path)
            except: pass
        if output_path.exists():
            try: os.remove(output_path)
            except: pass