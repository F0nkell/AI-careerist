import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from src.config import settings
from src.bot.handlers import router as bot_router

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- AIOGRAM SETUP ---
# Создаем экземпляр бота и диспетчера
bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()
dp.include_router(bot_router)

# Функция для установки команд бота
async def set_bot_commands(bot_instance: Bot):
    commands = [
        BotCommand(command="start", description="Начать работу / Проверить статус"),
        # Здесь будут другие команды
    ]
    await bot_instance.set_my_commands(commands)

# --- FASTAPI LIFESPAN (Управление жизненным циклом) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Контекстный менеджер для управления запуском/остановкой Aiogram.
    FastAPI запускает код в 'startup' и выполняет 'yield',
    а после остановки - код в 'shutdown'.
    """
    logger.info("Application startup: Setting up bot commands and starting polling...")
    
    # 1. Устанавливаем команды бота
    await set_bot_commands(bot)
    
    # 2. Запускаем polling в фоновом режиме
    # Мы используем asyncio.create_task, чтобы polling не блокировал FastAPI.
    polling_task = asyncio.create_task(dp.start_polling(bot))
    
    # FastAPI готов принимать запросы
    yield
    
    # --- SHUTDOWN ---
    logger.info("Application shutdown: Stopping bot polling...")
    # Отменяем задачу polling'а
    polling_task.cancel()
    try:
        await polling_task  # Ждем отмены
    except asyncio.exceptions.CancelledError:
        logger.info("Bot polling successfully stopped.")
    
    # Закрываем сессию бота
    await bot.session.close()


# --- FASTAPI SETUP ---
# Создаем экземпляр FastAPI с нашим lifespan
app = FastAPI(
    title="TWA Killer Core API",
    version="1.0.0",
    lifespan=lifespan,
)

# Базовый эндпоинт для проверки здоровья (Health Check)
@app.get("/health")
async def health_check():
    """Проверка здоровья API."""
    return {"status": "ok", "service": "Core API", "message": "FastAPI is running and ready."}

# Дополнительный эндпоинт для проверки статуса бота
@app.get("/bot_status")
async def bot_status():
    """Проверка, что бот авторизован."""
    try:
        me = await bot.get_me()
        return {"status": "ok", "bot_username": me.username, "message": "Aiogram is polling."}
    except Exception as e:
        return {"status": "error", "message": f"Bot API error: {e}"}

# Если мы будем использовать Webhooks, мы добавим здесь роут для /webhook
# Но для начала, Polling - самый простой способ проверки.