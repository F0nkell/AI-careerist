import asyncio
import json
import logging
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware  # <--- NEW: Для связи с фронтом
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.bot.handlers import router as bot_router
from src.database import get_db
from src.security import get_current_user
from src.schemas import InterviewAnswerRecord, InterviewSessionStartRequest, InterviewSessionState, TelegramUser
from src.services.audio_analysis import analyze_audio_file
from src.services.interview import process_voice_interview
from src.services.interview_evaluator import build_final_report, evaluate_answer
from src.services.interview_session import (
    audio_metrics_dict,
    create_interview_session,
    get_question_by_id,
    public_question,
)
from src.services.resume import process_resume_ai
from src.services.transcription import transcribe_audio_file

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
TEMP_AUDIO_DIR = Path("temp_audio")
TEMP_AUDIO_DIR.mkdir(exist_ok=True)

# --- AIOGRAM SETUP ---
bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()
dp.include_router(bot_router)

async def set_bot_commands(bot_instance: Bot):
    commands = [
        BotCommand(command="start", description="Начать работу"),
    ]
    await bot_instance.set_my_commands(commands)

# --- FASTAPI LIFESPAN ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Startup: Setting up bot...")
    await set_bot_commands(bot)
    polling_task = asyncio.create_task(dp.start_polling(bot))
    yield
    logger.info("Shutdown: Stopping bot...")
    polling_task.cancel()
    try:
        await polling_task
    except asyncio.exceptions.CancelledError:
        pass
    await bot.session.close()

# --- FASTAPI SETUP ---
app = FastAPI(
    title="TWA Killer Core API", 
    lifespan=lifespan,
    root_path="/api"  # Указываем, что мы сидим за прокси Nginx с префиксом /api
)

# --- CORS CONFIGURATION (NEW) ---
# Это критически важно. Мы разрешаем фронтенду (localhost:5173) стучаться к нам.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # <--- ЗВЕЗДОЧКА (Разрешить всем)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ENDPOINTS ---

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/bot_status")
async def bot_status():
    me = await bot.get_me()
    return {"status": "ok", "bot": me.username}

@app.get("/me")
async def get_my_profile(user: TelegramUser = Depends(get_current_user)):
    return {
        "status": "authenticated",
        "user": user.dict()
    }

@app.post("/resume/upload")
async def upload_resume(
    file: UploadFile = File(...),
    # Пока закомментируем проверку авторизации, чтобы тебе было легче тестить через Swagger
    # user: TelegramUser = Depends(get_current_user) 
):
    """
    Принимает PDF файл, проверяет формат и возвращает информацию о нем + разбор от ИИ.
    """
    # 1. Проверка формата
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    # Читаем файл
    content = await file.read()
    file_size_kb = len(content) / 1024

    logger.info(f"Received PDF: {file.filename}, Size: {file_size_kb:.2f} KB")

    # 3. Отправляем в ИИ
    ai_response = await process_resume_ai(file, content)

    return {
        "filename": file.filename,
        "size_kb": round(file_size_kb, 2),
        "message": "Анализ завершен",
        "ai_response": ai_response
    }

@app.post("/interview/chat")
async def interview_chat(
    file: UploadFile = File(...),
    image: UploadFile = File(None), # <--- Новое поле (необязательное)
    history: str = Form("[]")
):
    """
    Принимает голос + историю + (опционально) картинку.
    """
    try:
        # Передаем image в сервис
        result = await process_voice_interview(file, history, image)
        return result
    except Exception as e:
        logger.error(f"Interview error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def normalize_session_value(value: str | None, fallback: str) -> str:
    normalized = (value or fallback).strip().lower()
    if not normalized:
        raise HTTPException(status_code=400, detail="Interview profession and language must not be empty")
    return normalized


def parse_interview_session(session_json: str) -> InterviewSessionState:
    try:
        return InterviewSessionState.model_validate_json(session_json)
    except (ValidationError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail="Invalid interview session payload") from exc


async def save_answer_audio(file: UploadFile) -> Path:
    content = await file.read()
    if len(content) < 128:
        raise HTTPException(status_code=400, detail="Audio file is empty")

    suffix = Path(file.filename or "answer.webm").suffix or ".webm"
    audio_path = TEMP_AUDIO_DIR / f"{uuid.uuid4().hex}{suffix}"
    audio_path.write_bytes(content)
    return audio_path


def prior_interview_context(session_state: InterviewSessionState) -> list[dict]:
    context = []
    for answer in session_state.answers[-3:]:
        context.append(
            {
                "question_id": answer.question_id,
                "competency": answer.competency,
                "coverage_percent": answer.evaluation.get("coverage_percent"),
                "on_topic": answer.evaluation.get("on_topic"),
                "score_reason": answer.evaluation.get("score_reason"),
            }
        )
    return context


@app.post("/interview/session/start")
async def start_interview_session(
    payload: InterviewSessionStartRequest,
    db: AsyncSession = Depends(get_db),
):
    profession = normalize_session_value(payload.profession, settings.INTERVIEW_DEFAULT_PROFESSION)
    language = normalize_session_value(payload.language, settings.INTERVIEW_DEFAULT_LANGUAGE)

    try:
        session_state = await create_interview_session(db, profession, language)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return session_state.model_dump()


@app.post("/interview/session/answer")
async def answer_interview_question(
    session: str = Form(...),
    file: UploadFile = File(...),
    image: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
):
    _ = image
    session_state = parse_interview_session(session)
    if session_state.status != "active":
        raise HTTPException(status_code=400, detail="Interview session is already completed")

    if session_state.current_question_index >= len(session_state.selected_question_ids):
        raise HTTPException(status_code=400, detail="Interview session has no current question")

    question_id = session_state.selected_question_ids[session_state.current_question_index]
    question = await get_question_by_id(db, question_id)
    if question is None or not question.is_active:
        raise HTTPException(status_code=404, detail="Interview question not found")

    audio_path = await save_answer_audio(file)
    try:
        transcription = await transcribe_audio_file(audio_path)
        audio_metrics = analyze_audio_file(audio_path, transcription.transcript)
    finally:
        if audio_path.exists():
            audio_path.unlink()

    evaluation = await evaluate_answer(
        question=question,
        transcript=transcription.transcript,
        audio_metrics=audio_metrics,
        redirect_attempts=session_state.redirect_attempts,
        prior_context=prior_interview_context(session_state),
    )
    metrics_payload = audio_metrics_dict(audio_metrics)
    evaluation_payload = {
        **evaluation,
        "question_id": question.id,
        "competency": question.competency,
        "level": question.level,
        "difficulty": question.difficulty,
    }

    answer_record = InterviewAnswerRecord(
        question_id=question.id,
        competency=question.competency,
        level=question.level,
        difficulty=question.difficulty,
        transcript=transcription.transcript,
        audio_metrics=metrics_payload,
        evaluation=evaluation_payload,
        redirect_attempt=session_state.redirect_attempts,
    )
    session_state.answers.append(answer_record)
    session_state.evaluations.append(evaluation_payload)

    final_report = None
    if evaluation.get("should_redirect"):
        session_state.redirect_attempts += 1
        session_state.current_question = public_question(question)
        next_question = session_state.current_question
    else:
        session_state.redirect_attempts = 0
        session_state.current_question_index += 1

        if session_state.current_question_index >= len(session_state.selected_question_ids):
            session_state.status = "completed"
            session_state.current_question = None
            next_question = None
            final_report = await build_final_report(
                {
                    "session_id": session_state.session_id,
                    "profession": session_state.profession,
                    "language": session_state.language,
                    "question_count": len(session_state.selected_question_ids),
                    "evaluations": session_state.evaluations,
                }
            )
        else:
            next_question_model = await get_question_by_id(
                db,
                session_state.selected_question_ids[session_state.current_question_index],
            )
            if next_question_model is None:
                raise HTTPException(status_code=404, detail="Next interview question not found")
            session_state.current_question = public_question(next_question_model)
            next_question = session_state.current_question

    return {
        "session": session_state.model_dump(),
        "transcript": transcription.transcript,
        "transcription": {
            "provider": transcription.provider,
            "model": transcription.model,
            "duration": transcription.duration,
        },
        "audio_metrics": metrics_payload,
        "question_evaluation": evaluation_payload,
        "interviewer_message": evaluation_payload.get("final_feedback_to_user", ""),
        "next_question": next_question.model_dump() if next_question else None,
        "completed_report": final_report,
        "audio_base64": "",
    }
