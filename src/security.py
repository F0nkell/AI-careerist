import hmac
import hashlib
import json
import time
from urllib.parse import parse_qsl

from fastapi import HTTPException, Header, Depends, status
from pydantic import ValidationError

from src.config import settings
from src.schemas import TelegramUser

# Время жизни данных валидации (например, 1 день). 
# Чтобы старые перехваченные данные нельзя было использовать вечно.
AUTH_LIFETIME = 86400  

def validate_telegram_data(init_data: str) -> TelegramUser:
    """
    Валидирует данные initData от Telegram WebApp.
    Возвращает объект пользователя или вызывает ошибку 401.
    """
    try:
        # 1. Парсим query string в словарь
        parsed_data = dict(parse_qsl(init_data))
        
        # Проверяем наличие хеша
        received_hash = parsed_data.pop("hash", None)
        if not received_hash:
            raise ValueError("No hash found in initData")

        # 2. Проверка времени (auth_date)
        auth_date = int(parsed_data.get("auth_date", 0))
        if time.time() - auth_date > AUTH_LIFETIME:
             raise ValueError("InitData is outdated")

        # 3. Сортировка ключей (требование Telegram)
        # Формируем строку data_check_string: key=value\nkey=value...
        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(parsed_data.items())
        )

        # 4. Генерация Secret Key
        # HMAC-SHA256 от "WebAppData" с ключом = токен бота
        secret_key = hmac.new(
            key=b"WebAppData",
            msg=settings.BOT_TOKEN.encode(),
            digestmod=hashlib.sha256
        ).digest()

        # 5. Генерация хеша для проверки
        # HMAC-SHA256 от data_check_string с Secret Key
        calculated_hash = hmac.new(
            key=secret_key,
            msg=data_check_string.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()

        # 6. Сравнение хешей
        if calculated_hash != received_hash:
            raise ValueError("Invalid hash signature")

        # 7. Извлекаем данные пользователя (они приходят как JSON-строка)
        user_data_json = parsed_data.get("user")
        if not user_data_json:
            raise ValueError("No user data found")

        return TelegramUser(**json.loads(user_data_json))

    except (ValueError, ValidationError) as e:
        # Логируем ошибку для отладки (в реальном коде лучше logger.error)
        print(f"Auth Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# --- FASTAPI DEPENDENCY ---
# Эту функцию мы будем вставлять в аргументы эндпоинтов.
# Она ищет заголовок Authorization, достает оттуда initData и валидирует.

async def get_current_user(
    authorization: str = Header(..., description="String 'twa-init-data <initData>'")
) -> TelegramUser:
    """
    Извлекает initData из заголовка и валидирует её.
    Формат заголовка: Authorization: twa-init-data query_id=...&user=...
    """
    if not authorization.startswith("twa-init-data "):
        raise HTTPException(status_code=401, detail="Invalid header format")
    
    init_data_raw = authorization.split(" ", 1)[1]
    return validate_telegram_data(init_data_raw)