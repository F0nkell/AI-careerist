from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from src.database import Base


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"
    __table_args__ = (
        CheckConstraint("difficulty >= 1 AND difficulty <= 5", name="ck_interview_questions_difficulty"),
        CheckConstraint("level IN ('junior', 'middle', 'senior')", name="ck_interview_questions_level"),
        CheckConstraint("answer_time_limit_sec > 0", name="ck_interview_questions_answer_time_limit"),
        UniqueConstraint("code", name="uq_interview_questions_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(120), nullable=False, index=True)

    profession: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    language: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    competency: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    level: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False)

    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    expected_answer: Mapped[str] = mapped_column(Text, nullable=False)
    key_points: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    red_flags: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    follow_ups: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    evaluation_rubric: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    answer_time_limit_sec: Mapped[int] = mapped_column(Integer, nullable=False, default=120, server_default="120")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
