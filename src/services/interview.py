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
import speech_recognition as sr  # Google SR (Бесплатно)
from pydub import AudioSegment
import edge_tts 
from sqlalchemy import select, func

from src.config import settings
from src.database import AsyncSessionLocal
from src.models.question import Question

# --- НАСТРОЙКИ ---
# Используем Qwen VL (Vision Language) - он видит картинки
MODEL_NAME = "meta-llama/llama-3.2-90b-vision-instruct:free"
VOICE_NAME = "ru-RU-DmitryNeural"

# Клиент OpenRouter
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

def clean_text_for_speech(text: str) -> str:
    """
    Удаляет *действия*, (пояснения) и Markdown перед озвучкой.
    """
    cleaned = re.sub(r'\*.*?\*', '', text) 
    cleaned = re.sub(r'\(.*?\)', '', cleaned)
    cleaned = re.sub(r'```.*?```', 'код пропущен', cleaned, flags=re.DOTALL)
    cleaned = re.sub(r'`.*?`', '', cleaned) 
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

# --- RAG: Поиск вопросов в базе ---
async def get_rag_context(user_text: str) -> str:
    """
    Ищет ключевые слова в речи юзера и достает вопросы из БД.
    """
    category = "general"
    text = user_text.lower()
    
    # IT Сектор
    if "python" in text or "питон" in text:
        category = "python"
    elif "javascript" in text or "фронтенд" in text or "react" in text:
        category = "frontend"
    elif "java" in text:
        category = "java"
    elif "php" in text:
        category = "php"
    elif "sql" in text or "базы данных" in text:
        category = "sql"
    
    # Новые профессии
    elif "маркетолог" in text or "реклама" in text or "marketing" in text:
        category = "marketers"
    elif "врач" in text or "медик" in text or "доктор" in text or "медицина" in text:
        category = "medics"
    elif "учитель" in text or "педагог" in text or "преподаватель" in text or "школа" in text:
        category = "teachers"
    elif "бухгалтер" in text or "аудит" in text or "налоги" in text:
        category = "accountants"
    elif "инженер" in text or "конструктор" in text or "строитель" in text:
        category = "engineers"
    elif "психолог" in text or "терапия" in text:
        category = "psychologists"
    elif "экономист" in text or "финансы" in text:
        category = "economists"
    elif "менеджер" in text or "управленец" in text or "руководитель" in text:
        category = "managers"
        
    # Общие вопросы
    elif "hr" in text or "расскажи о себе" in text or "собеседование" in text:
        category = "hr"

    print(f"DEBUG: Detected category: {category}")

    async with AsyncSessionLocal() as session:
        query = select(Question.text).where(Question.category == category).order_by(func.random()).limit(3)
        result = await session.execute(query)
        questions = result.scalars().all()
        
        if not questions:
            print(f"DEBUG: No questions found for category '{category}'")
            return ""
            
        # Формируем текст шпаргалки
        rag_text = f"\n\n[RAG - РЕКОМЕНДОВАННЫЕ ВОПРОСЫ ИЗ БАЗЫ]:\n"
        for i, q in enumerate(questions, 1):
            rag_text += f"{i}. {q}\n"
        
        rag_text += "\n[ВАЖНО: Если вопросы выше на английском — ПЕРЕВЕДИ их и задавай ИСКЛЮЧИТЕЛЬНО НА РУССКОМ ЯЗЫКЕ!]\n"
        
        return rag_text

async def process_voice_interview(file: UploadFile, history_json: str, image: Optional[UploadFile] = None) -> dict:
    unique_id = uuid.uuid4().hex
    input_path = TEMP_DIR / f"{unique_id}.webm"
    wav_path = TEMP_DIR / f"{unique_id}.wav" # WAV нужен для Google Speech
    output_path = TEMP_DIR / f"{unique_id}_output.mp3"

    try:
        # 1. Обработка аудио (User Voice)
        content = await file.read()
        if len(content) < 1024:
            return {"user_text": "...", "ai_text": "Говорите громче.", "audio_base64": ""}
        with open(input_path, "wb") as f: f.write(content)

        # Конвертация WebM -> WAV (для Google SR)
        try:
            sound = AudioSegment.from_file(input_path)
            sound.export(wav_path, format="wav")
        except Exception as e:
            print(f"FFmpeg Error: {e}")
            return {"user_text": "Ошибка", "ai_text": "Проблема с аудиофайлом.", "audio_base64": ""}

        # 2. STT: Google Speech Recognition (Бесплатно, без ключа)
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

        # 3. Подготовка контекста (RAG + History)
        try: history = json.loads(history_json)
        except: history = []
        
        system_instruction = load_system_prompt()
        
        # Если юзер что-то сказал, ищем контекст в базе
        if user_text and user_text != "..." and user_text != "(Ошибка сервиса Google)":
            rag_context = await get_rag_context(user_text) 
            full_system = system_instruction + rag_context
        else:
            full_system = system_instruction

        messages = [{"role": "system", "content": full_system}]
        messages.extend(history)

        # 4. Формирование сообщения пользователя (Текст + Картинка)
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

        # 5. Запрос в Qwen (Vision)
        print(f"DEBUG: Sending to Qwen ({MODEL_NAME})...")
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            extra_headers={"HTTP-Referer": "https://t.me/ResumeKillerBot", "X-Title": "ResumeKiller"}
        )
        ai_text = response.choices[0].message.content
        print(f"DEBUG: AI said: {ai_text}")

        # 6. Озвучка (Edge TTS)
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