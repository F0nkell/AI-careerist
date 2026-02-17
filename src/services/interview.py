import os
import base64
import uuid
import json
import asyncio
import re
import random
from typing import List, Optional
from pathlib import Path
from fastapi import UploadFile
from openai import AsyncOpenAI
import speech_recognition as sr
from pydub import AudioSegment
import edge_tts 
from sqlalchemy import select, func

from src.config import settings
from src.database import AsyncSessionLocal
from src.models.question import Question

# --- НАСТРОЙКИ (Адаптировано под VseGPT) ---
# Вставь точный ID модели с VseGPT (например, google/gemini-2.5-flash-lite)
MODEL_NAME = "google/gemini-2.5-flash-lite" 
VOICE_NAME = "ru-RU-DmitryNeural" # Строгий мужской голос

# Клиент VseGPT
client = AsyncOpenAI(
    api_key=settings.OPENROUTER_API_KEY, # Используем старое имя переменной, но ключ VseGPT
    base_url="OPENROUTER_API_KEY"
)

TEMP_DIR = Path("temp_audio")
TEMP_DIR.mkdir(exist_ok=True)
PROMPT_PATH = Path("src/prompts/interview_master.txt")

def load_system_prompt():
    if PROMPT_PATH.exists():
        return PROMPT_PATH.read_text(encoding="utf-8")
    return "Ты строгий интервьюер. Пиши термины по-русски."

def clean_text_for_speech(text: str) -> str:
    """Чистит текст от *действий*, (пояснений) и Markdown перед озвучкой."""
    cleaned = re.sub(r'\*.*?\*', '', text) 
    cleaned = re.sub(r'\(.*?\)', '', cleaned)
    cleaned = re.sub(r'```.*?```', 'код пропущен', cleaned, flags=re.DOTALL)
    cleaned = re.sub(r'`.*?`', '', cleaned) 
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

# --- RAG: Поиск вопросов в базе ---
async def get_rag_context(user_text: str) -> str:
    category = "general"
    text = user_text.lower()
    
    # Определение категории (Полная версия)
    if "python" in text or "питон" in text: category = "python"
    elif "javascript" in text or "фронтенд" in text or "react" in text: category = "frontend"
    elif "java" in text: category = "java"
    elif "php" in text: category = "php"
    elif "sql" in text or "базы данных" in text: category = "sql"
    elif "маркетолог" in text or "реклама" in text or "marketing" in text: category = "marketers"
    elif "врач" in text or "медик" in text or "доктор" in text: category = "medics"
    elif "учитель" in text or "педагог" in text: category = "teachers"
    elif "бухгалтер" in text: category = "accountants"
    elif "инженер" in text: category = "engineers"
    elif "психолог" in text: category = "psychologists"
    elif "экономист" in text: category = "economists"
    elif "менеджер" in text or "управленец" in text: category = "managers"
    elif "hr" in text or "расскажи о себе" in text: category = "hr"

    print(f"DEBUG: Detected category: {category}")

    async with AsyncSessionLocal() as session:
        query = select(Question.text).where(Question.category == category).order_by(func.random()).limit(3)
        result = await session.execute(query)
        questions = result.scalars().all()
        
        if not questions:
            return ""
            
        rag_text = f"\n\n[RAG - РЕКОМЕНДОВАННЫЕ ВОПРОСЫ ИЗ БАЗЫ]:\n"
        for i, q in enumerate(questions, 1):
            rag_text += f"{i}. {q}\n"
        
        rag_text += "\n[ИНСТРУКЦИЯ: Если вопросы выше на английском — ПЕРЕВЕДИ их и задавай ИСКЛЮЧИТЕЛЬНО НА РУССКОМ ЯЗЫКЕ! Используй их, чтобы проверить кандидата.]\n"
        return rag_text

async def process_voice_interview(file: UploadFile, history_json: str, image: Optional[UploadFile] = None) -> dict:
    unique_id = uuid.uuid4().hex
    input_path = TEMP_DIR / f"{unique_id}.webm"
    wav_path = TEMP_DIR / f"{unique_id}.wav"
    output_path = TEMP_DIR / f"{unique_id}_output.mp3"

    try:
        try:
            history = json.loads(history_json)
        except:
            history = []

        # 1. Сохранение аудио
        content = await file.read()
        if len(content) < 1024:
            return {"user_text": "...", "ai_text": "Говорите громче.", "audio_base64": ""}

        with open(input_path, "wb") as f:
            f.write(content)

        # 2. Конвертация в WAV (для Google SR)
        try:
            sound = AudioSegment.from_file(input_path)
            sound.export(wav_path, format="wav")
        except Exception as e:
            print(f"FFmpeg Error: {e}")
            return {"user_text": "Ошибка", "ai_text": "Проблема с аудиофайлом.", "audio_base64": ""}

        # 3. Распознавание речи (Google Free)
        print("DEBUG: Sending audio to Google Speech...")
        r = sr.Recognizer()
        with sr.AudioFile(str(wav_path)) as source:
            r.adjust_for_ambient_noise(source, duration=0.5)
            audio_data = r.record(source)
            try:
                user_text = await asyncio.to_thread(r.recognize_google, audio_data, language="ru-RU")
            except sr.UnknownValueError:
                user_text = "..."
            except sr.RequestError:
                user_text = "(Ошибка сервиса Google)"
        
        print(f"DEBUG: User said: {user_text}")

        # 4. Сборка контекста (RAG + Промпт)
        system_instruction = load_system_prompt()
        
        if user_text and user_text != "..." and user_text != "(Ошибка сервиса Google)":
            rag_context = await get_rag_context(user_text) 
            full_system = system_instruction + rag_context
        else:
            full_system = system_instruction

        messages = [{"role": "system", "content": full_system}]
        messages.extend(history)

        # 5. Формирование сообщения (Текст + Картинка)
        user_content = []
        text_payload = user_text if (user_text and user_text != "...") else "Я молчал или был шум."
        user_content.append({"type": "text", "text": text_payload})

        if image:
            print(f"DEBUG: Processing image: {image.filename}")
            image_data = await image.read()
            base64_image = base64.b64encode(image_data).decode('utf-8')
            image_url = f"data:{image.content_type};base64,{base64_image}"
            
            user_content.append({
                "type": "image_url",
                "image_url": {"url": image_url}
            })

        messages.append({"role": "user", "content": user_content})

        # 6. Запрос к LLM (Gemini Flash)
        print(f"DEBUG: Sending to LLM ({MODEL_NAME})...")
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            extra_headers={"HTTP-Referer": "https://t.me/ResumeKillerBot", "X-Title": "ResumeKiller"}
        )
        ai_text = response.choices[0].message.content
        print(f"DEBUG: AI said: {ai_text}")

        # 7. Озвучка (Edge TTS - Дмитрий)
        speech_text = clean_text_for_speech(ai_text)
        if speech_text:
            communicate = edge_tts.Communicate(speech_text, VOICE_NAME)
            await communicate.save(str(output_path))
        
        if output_path.exists():
            with open(output_path, "rb") as audio_file:
                audio_base64 = base64.b64encode(audio_file.read()).decode('utf-8')
        else:
            audio_base64 = ""

        return {
            "user_text": user_text,
            "ai_text": ai_text,
            "audio_base64": audio_base64
        }

    except Exception as e:
        print(f"Global Error: {e}")
        return {"user_text": "Error", "ai_text": f"Ошибка: {str(e)}", "audio_base64": ""}

    finally:
        for p in [input_path, wav_path, output_path]:
            if p.exists(): 
                try: os.remove(p)
                except: pass
