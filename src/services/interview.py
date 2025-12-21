import os
import base64
import uuid
import json
import asyncio
from typing import List
from pathlib import Path
from fastapi import UploadFile
from openai import AsyncOpenAI
import speech_recognition as sr
from pydub import AudioSegment
from gtts import gTTS

from src.config import settings

client = AsyncOpenAI(
    api_key=settings.OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

TEMP_DIR = Path("temp_audio")
TEMP_DIR.mkdir(exist_ok=True)
PROMPT_PATH = Path("src/prompts/interview_master.txt")

def load_system_prompt():
    if PROMPT_PATH.exists():
        return PROMPT_PATH.read_text(encoding="utf-8")
    return "Ты строгий интервьюер."

# --- ОБНОВЛЕННАЯ СИГНАТУРА ФУНКЦИИ ---
async def process_voice_interview(file: UploadFile, history_json: str) -> dict:
    unique_id = uuid.uuid4().hex
    input_path = TEMP_DIR / f"{unique_id}.webm"
    wav_path = TEMP_DIR / f"{unique_id}.wav"
    output_path = TEMP_DIR / f"{unique_id}_output.mp3"

    try:
        # 1. Парсим историю (Приходит как строка JSON)
        try:
            history = json.loads(history_json)
        except:
            history = []

        # 2. Обработка аудио
        content = await file.read()
        if len(content) < 1024:
            return {"user_text": "...", "ai_text": "Говорите громче.", "audio_base64": ""}

        with open(input_path, "wb") as f:
            f.write(content)

        try:
            sound = AudioSegment.from_file(input_path)
            sound.export(wav_path, format="wav")
        except Exception:
            return {"user_text": "Error", "ai_text": "Ошибка аудио.", "audio_base64": ""}

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
             return {"user_text": "...", "ai_text": "Повторите, я не расслышал.", "audio_base64": ""}

        # 3. СБОРКА КОНТЕКСТА (System + History + User)
        system_instruction = load_system_prompt()
        
        # Формируем полный список сообщений для ИИ
        messages_payload = [{"role": "system", "content": system_instruction}]
        
        # Добавляем историю (последние 10 сообщений)
        # Важно: history приходит в формате [{role: "user", content: "..."}, ...]
        messages_payload.extend(history)
        
        # Добавляем текущий вопрос
        messages_payload.append({"role": "user", "content": user_text})

        # 4. Запрос к DeepSeek
        response = await client.chat.completions.create(
            model="deepseek/deepseek-chat",
            messages=messages_payload,
            extra_headers={
                "HTTP-Referer": "https://t.me/ResumeKillerBot", 
                "X-Title": "ResumeKiller",
            }
        )
        ai_text = response.choices[0].message.content
        print(f"DEBUG: AI said: {ai_text}")

        # 5. Озвучка
        def save_tts():
            tts = gTTS(text=ai_text, lang='ru')
            tts.save(str(output_path))
        
        await asyncio.to_thread(save_tts)

        with open(output_path, "rb") as audio_file:
            audio_base64 = base64.b64encode(audio_file.read()).decode('utf-8')

        return {
            "user_text": user_text,
            "ai_text": ai_text,
            "audio_base64": audio_base64
        }

    except Exception as e:
        print(f"Global Error: {e}")
        return {"user_text": "Error", "ai_text": "Ошибка сервера.", "audio_base64": ""}

    finally:
        for p in [input_path, wav_path, output_path]:
            if p.exists():
                try: os.remove(p)
                except: pass