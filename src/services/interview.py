import os
import base64
import uuid
import asyncio
from pathlib import Path
from fastapi import UploadFile
from openai import AsyncOpenAI
import speech_recognition as sr
from pydub import AudioSegment
from gtts import gTTS

from src.config import settings

# Клиент OpenRouter
client = AsyncOpenAI(
    api_key=settings.OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

TEMP_DIR = Path("temp_audio")
TEMP_DIR.mkdir(exist_ok=True)

async def process_voice_interview(file: UploadFile) -> dict:
    unique_id = uuid.uuid4().hex
    
    # Важно: Сохраняем с расширением .webm (стандарт браузеров), 
    # чтобы ffmpeg понимал, с чем работает.
    input_path = TEMP_DIR / f"{unique_id}.webm"
    wav_path = TEMP_DIR / f"{unique_id}.wav"
    output_path = TEMP_DIR / f"{unique_id}_output.mp3"

    try:
        # 1. Читаем файл
        content = await file.read()
        
        # --- ВАЛИДАЦИЯ (ЗАЩИТА ОТ ПУСТЫХ ФАЙЛОВ) ---
        file_size = len(content)
        print(f"DEBUG: Received file size: {file_size} bytes")
        
        if file_size < 1024: # Если меньше 1 КБ
            print("DEBUG: File too small, skipping.")
            return {
                "user_text": "...",
                "ai_text": "Я не расслышал. Нажмите кнопку и удерживайте её, пока говорите.",
                "audio_base64": "" # Можно вернуть тишину или спец. звук
            }
        # -------------------------------------------

        # Сохраняем
        with open(input_path, "wb") as f:
            f.write(content)

        # 2. Конвертация (pydub)
        # Мы явно указываем format="webm", так как браузеры (Chrome/Telegram) шлют webm
        try:
            sound = AudioSegment.from_file(input_path) 
            sound.export(wav_path, format="wav")
        except Exception as e:
            print(f"FFmpeg Error: {e}")
            return {
                "user_text": "(Ошибка аудио)",
                "ai_text": "Не удалось обработать аудиофайл. Попробуйте еще раз.",
                "audio_base64": ""
            }

        # 3. Распознавание (Google Speech)
        r = sr.Recognizer()
        with sr.AudioFile(str(wav_path)) as source:
            # Очищаем шум (полезно для микрофона)
            r.adjust_for_ambient_noise(source, duration=0.5)
            audio_data = r.record(source)
            
            try:
                user_text = await asyncio.to_thread(r.recognize_google, audio_data, language="ru-RU")
            except sr.UnknownValueError:
                user_text = "..."
            except sr.RequestError:
                user_text = "(Ошибка сервиса STT)"

        print(f"DEBUG: User said: {user_text}")

        # Если пользователь молчал или шум
        if not user_text or user_text == "...":
             return {
                "user_text": "...",
                "ai_text": "Я вас не слышу. Повторите, пожалуйста.",
                "audio_base64": ""
            }

        # 4. Мозг (DeepSeek via OpenRouter)
        response = await client.chat.completions.create(
            model="deepseek/deepseek-chat",
            messages=[
                {"role": "system", "content": "Ты строгий HR-менеджер. Отвечай на русском, кратко (1-2 предложения)."},
                {"role": "user", "content": user_text},
            ],
            extra_headers={
                "HTTP-Referer": "https://t.me/ResumeKillerBot", 
                "X-Title": "ResumeKiller",
            }
        )
        ai_text = response.choices[0].message.content
        print(f"DEBUG: AI said: {ai_text}")

        # 5. Озвучка (gTTS)
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
        print(f"Global Error: {e}")
        return {
            "user_text": "Ошибка",
            "ai_text": "Произошла ошибка сервера.",
            "audio_base64": ""
        }

    finally:
        for p in [input_path, wav_path, output_path]:
            if p.exists():
                try: os.remove(p)
                except: pass