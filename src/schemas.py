from pydantic import BaseModel, Field

# Модель пользователя внутри initData (Telegram присылает JSON внутри строки)
class TelegramUser(BaseModel):
    id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    language_code: str | None = None
    is_premium: bool | None = False
    allows_write_to_pm: bool | None = False

# Модель данных авторизации, которые мы ждем от фронтенда
class TelegramAuthData(BaseModel):
    initData: str = Field(..., description="Raw query string from Telegram WebApp")