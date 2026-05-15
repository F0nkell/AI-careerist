from typing import Any, Literal

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


class InterviewSessionStartRequest(BaseModel):
    profession: str = Field(default="backend", min_length=1)
    language: str | None = Field(default="python")


class InterviewQuestionPublic(BaseModel):
    id: int
    profession: str
    language: str | None
    competency: str
    level: str
    difficulty: int
    question_text: str
    answer_time_limit_sec: int


class InterviewAnswerRecord(BaseModel):
    question_id: int
    competency: str
    level: str
    difficulty: int
    transcript: str
    audio_metrics: dict[str, Any]
    evaluation: dict[str, Any]
    redirect_attempt: int


class InterviewSessionState(BaseModel):
    session_id: str
    profession: str
    language: str | None
    selected_question_ids: list[int]
    current_question_index: int
    current_question: InterviewQuestionPublic | None
    redirect_attempts: int = 0
    answers: list[InterviewAnswerRecord] = Field(default_factory=list)
    evaluations: list[dict[str, Any]] = Field(default_factory=list)
    status: Literal["active", "completed"] = "active"
