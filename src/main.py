import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware  # <--- NEW: Для связи с фронтом
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from src.config import settings
from src.bot.handlers import router as bot_router
from src.security import get_current_user
from src.schemas import TelegramUser
from src.services.interview import process_voice_interview

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- AIOGRAM SETUP ---
bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()
dp.include_router(bot_router)

async def set_bot_commands(bot_instance: Bot):
    commands = [
        BotCommand(command="start", description="Начать работу"),
    ]
    await bot_instance.set_my_commands(commands)

# --- FASTAPI LIFESPAN ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Startup: Setting up bot...")
    await set_bot_commands(bot)
    polling_task = asyncio.create_task(dp.start_polling(bot))
    yield
    logger.info("Shutdown: Stopping bot...")
    polling_task.cancel()
    try:
        await polling_task
    except asyncio.exceptions.CancelledError:
        pass
    await bot.session.close()

# --- FASTAPI SETUP ---
app = FastAPI(title="TWA Killer Core API", lifespan=lifespan)

# --- CORS CONFIGURATION (NEW) ---
# Это критически важно. Мы разрешаем фронтенду (localhost:5173) стучаться к нам.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # <--- ЗВЕЗДОЧКА (Разрешить всем)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ENDPOINTS ---

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/bot_status")
async def bot_status():
    me = await bot.get_me()
    return {"status": "ok", "bot": me.username}

@app.get("/me")
async def get_my_profile(user: TelegramUser = Depends(get_current_user)):
    return {
        "status": "authenticated",
        "user": user.dict()
    }

# --- RESUME UPLOAD ENDPOINT (NEW) ---
@app.post("/resume/upload")
async def upload_resume(
    file: UploadFile = File(...),
    # Пока закомментируем проверку авторизации, чтобы тебе было легче тестить через Swagger
    # user: TelegramUser = Depends(get_current_user) 
):
    """
    Принимает PDF файл, проверяет формат и возвращает информацию о нем.
    В будущем здесь будет запуск AI-анализа.
    """
    # 1. Проверка формата
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    # 2. (Симуляция) Читаем файл (в будущем будем парсить текст)
    content = await file.read()
    file_size_kb = len(content) / 1024

    logger.info(f"Received PDF: {file.filename}, Size: {file_size_kb:.2f} KB")

    return {
        "filename": file.filename,
        "size_kb": round(file_size_kb, 2),
        "message": "File received successfully. AI processing will be here."
    }

@app.post("/interview/chat")
async def interview_chat(
    file: UploadFile = File(...),
    image: UploadFile = File(None), # <--- Новое поле (необязательное)
    history: str = Form("[]")
):
    """
    Принимает голос + историю + (опционально) картинку.
    """
    try:
        # Передаем image в сервис
        result = await process_voice_interview(file, history, image)
        return result
    except Exception as e:
        logger.error(f"Interview error: {e}")
        raise HTTPException(status_code=500, detail=str(e))