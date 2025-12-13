from datetime import datetime
from sqlalchemy import BigInteger, String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from src.database import Base

class User(Base):
    __tablename__ = "users"

    # Telegram ID может быть больше 2^31, поэтому используем BigInteger
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    username: Mapped[str | None] = mapped_column(String, nullable=True)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str | None] = mapped_column(String, nullable=True)
    
    # Флаг для премиум доступа или бана
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Время создания и обновления
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"