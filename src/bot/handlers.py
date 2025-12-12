from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

# Создаем роутер для регистрации обработчиков.
# Это позволяет нам модульно подключать логику.
router = Router()

# Обработчик команды /start
@router.message(Command("start"))
async def command_start_handler(message: Message) -> None:
    """Обрабатывает команду /start и приветствует пользователя."""
    await message.answer(
        f"Привет, {message.from_user.full_name}! Я - твой Resume Killer и Mock Interviewer. "
        "Ядро запущено (FastAPI + Aiogram)."
    )

# Эхо-обработчик
@router.message()
async def echo_handler(message: Message) -> None:
    """Простой эхо-ответ на любое сообщение."""
    try:
        await message.send_copy(chat_id=message.chat.id)
    except TypeError:
        # Если сообщение нельзя скопировать (например, стикер), просто игнорируем
        pass