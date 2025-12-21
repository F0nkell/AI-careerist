import os
import base64
import uuid
import json
import asyncio
import random
from typing import List
from pathlib import Path
from fastapi import UploadFile
from openai import AsyncOpenAI
import speech_recognition as sr
from pydub import AudioSegment
from gtts import gTTS
from sqlalchemy import select, func

from src.config import settings
from src.database import AsyncSessionLocal
from src.models.question import Question

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
    
    # Новые профессии (Custom JSON)
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
            
        # Формируем текст шпаргалки С ПРИНУЖДЕНИЕМ К РУССКОМУ
        rag_text = f"\n\n[RAG - РЕКОМЕНДОВАННЫЕ ВОПРОСЫ ИЗ БАЗЫ]:\n"
        for i, q in enumerate(questions, 1):
            rag_text += f"{i}. {q}\n"
        
        # <--- ДОБАВЛЯЕМ ЭТУ СТРОКУ --->
        rag_text += "\n[ВАЖНО: Если вопросы выше на английском — ПЕРЕВЕДИ их и задавай ИСКЛЮЧИТЕЛЬНО НА РУССКОМ ЯЗЫКЕ!]\n"
        
        return rag_text

async def process_voice_interview(file: UploadFile, history_json: str) -> dict:
    unique_id = uuid.uuid4().hex
    input_path = TEMP_DIR / f"{unique_id}.webm"
    wav_path = TEMP_DIR / f"{unique_id}.wav"
    output_path = TEMP_DIR / f"{unique_id}_output.mp3"

    try:
        try:
            history = json.loads(history_json)
        except:
            history = []

        content = await file.read()
        if len(content) < 1024:
            return {"user_text": "...", "ai_text": "Говорите громче.", "audio_base64": ""}

        with open(input_path, "wb") as f:
            f.write(content)

        try:
            sound = AudioSegment.from_file(input_path)
            sound.export(wav_path, format="wav")
        except:
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
             return {"user_text": "...", "ai_text": "Повторите.", "audio_base64": ""}

        # --- СБОРКА ПРОМПТА С RAG ---
        base_instruction = load_system_prompt()
        rag_context = await get_rag_context(user_text) # Ищем вопросы в базе
        
        full_system_prompt = base_instruction + rag_context
        
        print(f"DEBUG: RAG Context added: {len(rag_context)} chars")

        messages_payload = [{"role": "system", "content": full_system_prompt}]
        messages_payload.extend(history)
        messages_payload.append({"role": "user", "content": user_text})

        response = await client.chat.completions.create(
            model="deepseek/deepseek-chat",
            messages=messages_payload,
            extra_headers={"HTTP-Referer": "https://t.me/ResumeKillerBot", "X-Title": "ResumeKiller"}
        )
        ai_text = response.choices[0].message.content
        print(f"DEBUG: AI said: {ai_text}")

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