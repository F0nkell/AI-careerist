from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from src.config import settings

# Формируем URL подключения.
# Важно: используем драйвер postgresql+asyncpg для асинхронной работы.
DATABASE_URL = (
    f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@"
    f"{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
)

# Создаем движок (Engine)
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Ставь True, если хочешь видеть SQL запросы в консоли
)

# Создаем фабрику сессий
# expire_on_commit=False обязателен для асинхронной работы
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Базовый класс для всех моделей
class Base(DeclarativeBase):
    pass

# Dependency для FastAPI
# Позволяет получать сессию БД в каждом эндпоинте: async def handler(db: AsyncSession = Depends(get_db))
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()