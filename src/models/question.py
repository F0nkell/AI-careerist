from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base

class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    category: Mapped[str] = mapped_column(String, index=True) # python, hr, etc
    level: Mapped[str] = mapped_column(String, default="all") # junior, middle
    text: Mapped[str] = mapped_column(Text, nullable=False)
    expected_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str | None] = mapped_column(String, nullable=True)