import io
import re
from fastapi import UploadFile
from openai import AsyncOpenAI
import pypdf

from src.config import settings

# --- НАСТРОЙКИ ---
# Используем быструю и дешевую модель (можно поменять на google/gemini-2.5-flash-lite как в интервью)
MODEL_NAME = settings.OPENROUTER_CHAT_MODEL

client = AsyncOpenAI(
    api_key=settings.vsegpt_api_key,
    base_url=settings.vsegpt_base_url
)

SYSTEM_PROMPT = """
Ты — Senior-разработчик с 15-летним стажем, делающий жесткое ревью. Твоя задача — проанализировать текст глубоко, построчно.

ИНСТРУКЦИЯ ПО АНАЛИЗУ:
1. Сначала ОБЯЗАТЕЛЬНО начни свой ответ с тега <think> и закончи его </think>. Внутри этих тегов ты будешь размышлять (пользователь этого не увидит):
   - Прочитай текст вдумчиво. 
   - Сделай выжимку: о чем этот текст? (Это реальное резюме? Это рецепт пельменей, куда вставили слова "многопоточность"? Это банковский чек о переводе рублей? Это бессмысленный набор букв?). Впиши честную выжимку, как ты это видишь.
   - Выпиши РЕАЛЬНЫЙ стек технологий и опыт автора напрямую из текста.
   - Если это резюме, определи 2-3 главные ошибки (много воды, нет бизнес-результатов, пишет "мы" вместо "я", и т.д.), опираясь СТРОГО на собранные из текста факты.

2. Сразу после закрывающего тега </think> выдай финальный ответ пользователю в твоем токсично-циничном стиле "уставшего Сеньора".

ПРАВИЛА ИТОГОВОГО ОТВЕТА (Пишется ПОСЛЕ </think>):
- Если внутри <think> ты понял, что текст — это бред, чек, рецепт или мусор, ответь коротко и дерзко: "Ты мне что, квитанцию / рецепт пельменей прислал? Я тебе HR или мусорка?". И СРАЗУ ЗАВЕРШИ ОТВЕТ. Не выдумывай советы по IT-решениям для мусорных текстов.
- Если внутри <think> ты подтвердил, что это резюме: разнеси кандидата за реальные фразы из текста. ЗАПРЕЩАЕТСЯ критиковать то, чего нет (если в резюме нет ни слова про SQL или C# — не упоминай их).
- Разнеси его пренебрежительно, но в самом конце дай 1 поучительный, дельный совет, как переделать именно его опыт во что-то стоящее.
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
        content = response.choices[0].message.content
        
        # Вырезаем внутренние размышления бота (<think>...</think>), чтобы показать юзеру только суть
        final_answer = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
        
        # Если вдруг бот прислал только <think> (сбой), отдадим оригинальный текст очищенный от тега
        if not final_answer:
            final_answer = content.replace("<think>", "").replace("</think>", "").strip()
            
        return final_answer
    except Exception as e:
        print(f"LLM Error: {e}")
        return "Слушай, от твоего резюме даже наша серверная нейронка легла (ошибка API). Попробуй закинуть еще раз позже."
