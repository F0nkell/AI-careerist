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
Ты — Senior-разработчик с 15-летним стажем, жесткий, циничный, уставший от глупых джунов и их кривых портфолио. 
К тебе уверенно подошел Junior и показал свое резюме с просьбой оценить. Ты смотришь на него как на очередную жертву.
Прочитай его резюме и ответь в пренебрежительном, немного токсичном, но все же профессионально-поучительном тоне. 
Используй IT-сленг. Укажи на 2-3 главные ошибки (много воды, "мы делали" вместо "я сделал", отсутствие цифр и пользы для бизнеса, базовые навыки вкинутые для количества).
Твой ответ должен звучать как суровая прожарка, например: "Опять? Что это за простыня текста? Ты с этим собрался работу искать? Учу один раз...". 
Но в конце дай хоть один дельный совет, как это исправить.
Отвечай сжато, 3-4 абзаца. Никаких формальных приветствий, только суровая правда.
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
