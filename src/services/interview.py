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

# Путь к файлу с инструкцией
PROMPT_PATH = Path("src/prompts/interview_master.txt")

def load_system_prompt():
    """Читает инструкцию из файла. Если файла нет, берет дефолт."""
    if PROMPT_PATH.exists():
        return PROMPT_PATH.read_text(encoding="utf-8")
    return "Ты строгий интервьюер. Отвечай кратко."

async def process_voice_interview(file: UploadFile) -> dict:
    unique_id = uuid.uuid4().hex
    input_path = TEMP_DIR / f"{unique_id}.webm"
    wav_path = TEMP_DIR / f"{unique_id}.wav"
    output_path = TEMP_DIR / f"{unique_id}_output.mp3"

    try:
        # 1. Читаем и валидируем файл
        content = await file.read()
        if len(content) < 1024:
            return {
                "user_text": "...",
                "ai_text": "Слишком короткое сообщение. Нажмите и удерживайте кнопку.",
                "audio_base64": ""
            }

        with open(input_path, "wb") as f:
            f.write(content)

        # 2. Конвертация (WebM -> WAV)
        try:
            sound = AudioSegment.from_file(input_path)
            sound.export(wav_path, format="wav")
        except Exception as e:
            print(f"FFmpeg Error: {e}")
            return {"user_text": "Ошибка аудио", "ai_text": "Не удалось прочитать файл.", "audio_base64": ""}

        # 3. Распознавание (STT)
        r = sr.Recognizer()
        with sr.AudioFile(str(wav_path)) as source:
            r.adjust_for_ambient_noise(source, duration=0.5)
            audio_data = r.record(source)
            try:
                user_text = await asyncio.to_thread(r.recognize_google, audio_data, language="ru-RU")
            except:
                user_text = "..."

        print(f"DEBUG: User said: {user_text}")

        if not user_text or user_text == "...":
             return {"user_text": "...", "ai_text": "Я вас не слышу. Повторите.", "audio_base64": ""}

        # 4. Мозг (DeepSeek + System Prompt из файла)
        # Загружаем актуальную инструкцию
        system_instruction = load_system_prompt()
        
        response = await client.chat.completions.create(
            model="deepseek/deepseek-chat",
            messages=[
                {"role": "system", "content": system_instruction}, # <--- ВОТ ОНА
                {"role": "user", "content": user_text},
            ],
            extra_headers={
                "HTTP-Referer": "https://t.me/ResumeKillerBot", 
                "X-Title": "ResumeKiller",
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
        print(f"Global Error: {e}")
        return {"user_text": "Ошибка", "ai_text": "Ошибка сервера.", "audio_base64": ""}

    finally:
        for p in [input_path, wav_path, output_path]:
            if p.exists():
                try: os.remove(p)
                except: pass