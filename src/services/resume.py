import io
import asyncio
from fastapi import UploadFile
from openai import AsyncOpenAI
import pypdf

from src.config import settings

# --- НАСТРОЙКИ ---
# Используем быструю и дешевую модель (можно поменять на google/gemini-2.5-flash-lite как в интервью)
MODEL_NAME = "openai/gpt-4o-mini" 

client = AsyncOpenAI(
    api_key=settings.OPENROUTER_API_KEY, 
    base_url="https://api.vsegpt.ru/v1"
)

SYSTEM_PROMPT = """
Ты — Senior-разработчик с 15-летним стажем, проводящий ревью резюме. Твой стиль — жесткий, циничный, токсичный, но ты всегда бьешь только по реальным фактам.

Твоя задача — провести глубокий анализ переданного текста. Анализируй вдумчиво, строку за строкой.

ШАГ 1: Валидация документа (КРИТИЧЕСКИ ВАЖНО!)
Определи, действительно ли это резюме. Люди могут пытаться обмануть тебя, присылая рецепты пельменей с IT-терминами (например: "оптимизировал варку пельменей в два потока"), чеки о переводе, платежки или бессмысленный текст. 
Действие: Если это чек, пустой текст, стишок или рецепт — осади пользователя: "Ты мне что, квитанцию / рецепт пельменей прислал? Я тебе HR или мусорка? Иди ищи свое резюме, клоун." И СРАЗУ ЗАВЕРШИ ОТВЕТ. Не давай никаких советов по языкам программирования.

ШАГ 2: Жесткий разбор реального резюме (Только если Шаг 1 пройден успешно)
Обдумай весь текст и выдели 2-3 реальные ошибки, опираясь СТРОГО на написанное.
- ЗАПРЕЩЕНО придумывать термины или навыки (не приплетай C# или SQL, если их нет в тексте).
- Если кандидат пишет "мы разрабатывали" — разнеси его за то, что он прячется за командой.
- Если в тексте нет метрик, бизнес-показателей и цифр — назови это пустой водой, которая полетит в урну скриптом автофильтрации.

ШАГ 3: Суровая правда
Разнеси его пренебрежительно, но в конце дай один четкий дельный совет, как переделать именно его стек и опыт в продающий формат. Выдавай ответ в 3-4 абзаца. Никаких приветствий.
"""

async def extract_text_from_pdf(file_content: bytes) -> str:
    text = ""
    try:
        # pypdf работает с файлоподобными объектами
        pdf_file = io.BytesIO(file_content)
        reader = pypdf.PdfReader(pdf_file)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        return "ПДФку то я не смог открыть. Что за кодировка? Это скан? Переделай в нормальный парсящийся PDF, я тебе не Ванга."
    return text.strip()

async def process_resume_ai(file: UploadFile, file_content: bytes) -> str:
    try:
        resume_text = await extract_text_from_pdf(file_content)
        
        # Если текста слишком мало
        if not resume_text or len(resume_text) < 20:
            return "Что это за пустота? Ты бы еще белый лист принес. Или это скриншот? Я тебе что, OCR-машина? Иди экспортируй свой Word в нормальный PDF с текстом, потом приходи."

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Вот мое резюме, глянь плиз:\n\n{resume_text}"}
        ]

        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            extra_headers={"HTTP-Referer": "https://t.me/ResumeKillerBot", "X-Title": "ResumeKiller"}
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"LLM Error: {e}")
        return "Слушай, от твоего резюме даже наша серверная нейронка легла (ошибка API). Попробуй закинуть еще раз позже."
