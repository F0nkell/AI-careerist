from pydantic_settings import BaseSettings, SettingsConfigDict

# Класс настроек, который автоматически загружает переменные из .env
# и проверяет их типы. Это надежно и чисто.
class Settings(BaseSettings):
    # Основные настройки
    BOT_TOKEN: str
    API_PORT: int = 8000
    SECRET_KEY: str

    # Настройки базы данных (для Этапа 2)
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int

    # Указываем, что нужно искать файл .env
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

# Создаем единственный экземпляр настроек
settings = Settings()