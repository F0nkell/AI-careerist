import uuid
from dataclasses import asdict
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.models.interview_question import InterviewQuestion
from src.schemas import InterviewQuestionPublic, InterviewSessionState


QUESTION_PLAN: tuple[tuple[tuple[str, ...], tuple[str, ...], int], ...] = (
    (("python_core",), ("junior", "middle"), 2),
    (("async",), ("middle", "junior"), 3),
    (("fastapi",), ("junior", "middle"), 3),
    (("databases",), ("middle", "senior"), 4),
    (("architecture",), ("middle", "senior"), 4),
    (("testing",), ("junior", "middle", "senior"), 3),
    (("security", "devops"), ("middle", "senior", "junior"), 4),
)


LEVEL_ORDER = {
    "junior": 1,
    "middle": 2,
    "senior": 3,
}


def public_question(question: InterviewQuestion) -> InterviewQuestionPublic:
    return InterviewQuestionPublic(
        id=question.id,
        profession=question.profession,
        language=question.language,
        competency=question.competency,
        level=question.level,
        difficulty=question.difficulty,
        question_text=question.question_text,
        answer_time_limit_sec=question.answer_time_limit_sec,
    )


def level_rank(level: str) -> int:
    return LEVEL_ORDER.get(level, 99)


def candidate_score(
    question: InterviewQuestion,
    preferred_levels: Iterable[str],
    target_difficulty: int,
    competency_counts: dict[str, int],
) -> tuple[int, int, int, int]:
    preferred_level_list = list(preferred_levels)
    try:
        level_distance = preferred_level_list.index(question.level)
    except ValueError:
        level_distance = len(preferred_level_list) + abs(level_rank(question.level) - 2)

    return (
        competency_counts.get(question.competency, 0),
        level_distance,
        abs(question.difficulty - target_difficulty),
        question.id,
    )


def pick_best_question(
    candidates: list[InterviewQuestion],
    competencies: tuple[str, ...],
    preferred_levels: tuple[str, ...],
    target_difficulty: int,
    selected_ids: set[int],
    competency_counts: dict[str, int],
) -> InterviewQuestion | None:
    matching = [
        question
        for question in candidates
        if question.id not in selected_ids and question.competency in competencies
    ]
    if not matching:
        return None
    return min(
        matching,
        key=lambda item: candidate_score(item, preferred_levels, target_difficulty, competency_counts),
    )


def fill_remaining_questions(
    candidates: list[InterviewQuestion],
    selected: list[InterviewQuestion],
    question_count: int,
) -> list[InterviewQuestion]:
    selected_ids = {question.id for question in selected}
    competency_counts: dict[str, int] = {}
    for question in selected:
        competency_counts[question.competency] = competency_counts.get(question.competency, 0) + 1

    remaining = [question for question in candidates if question.id not in selected_ids]
    remaining.sort(
        key=lambda item: (
            competency_counts.get(item.competency, 0),
            abs(item.difficulty - 3),
            level_rank(item.level),
            item.id,
        )
    )
    return selected + remaining[: max(0, question_count - len(selected))]


def select_interview_questions(candidates: list[InterviewQuestion], question_count: int) -> list[InterviewQuestion]:
    selected: list[InterviewQuestion] = []
    selected_ids: set[int] = set()
    competency_counts: dict[str, int] = {}

    for competencies, preferred_levels, target_difficulty in QUESTION_PLAN:
        if len(selected) >= question_count:
            break

        question = pick_best_question(
            candidates,
            competencies,
            preferred_levels,
            target_difficulty,
            selected_ids,
            competency_counts,
        )
        if question is None:
            continue

        selected.append(question)
        selected_ids.add(question.id)
        competency_counts[question.competency] = competency_counts.get(question.competency, 0) + 1

    return fill_remaining_questions(candidates, selected, question_count)[:question_count]


async def load_active_questions(
    db: AsyncSession,
    profession: str,
    language: str | None,
) -> list[InterviewQuestion]:
    query = (
        select(InterviewQuestion)
        .where(
            InterviewQuestion.profession == profession,
            InterviewQuestion.language == language,
            InterviewQuestion.is_active.is_(True),
        )
        .order_by(
            InterviewQuestion.competency.asc(),
            InterviewQuestion.difficulty.asc(),
            InterviewQuestion.id.asc(),
        )
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_interview_session(
    db: AsyncSession,
    profession: str,
    language: str | None,
) -> InterviewSessionState:
    candidates = await load_active_questions(db, profession, language)
    if len(candidates) < settings.INTERVIEW_QUESTION_COUNT:
        raise ValueError(
            f"Not enough active questions for profession={profession}, language={language}. "
            f"Need {settings.INTERVIEW_QUESTION_COUNT}, got {len(candidates)}."
        )

    selected = select_interview_questions(candidates, settings.INTERVIEW_QUESTION_COUNT)
    if len(selected) < settings.INTERVIEW_QUESTION_COUNT:
        raise ValueError(
            f"Could not select {settings.INTERVIEW_QUESTION_COUNT} interview questions."
        )

    return InterviewSessionState(
        session_id=uuid.uuid4().hex,
        profession=profession,
        language=language,
        selected_question_ids=[question.id for question in selected],
        current_question_index=0,
        current_question=public_question(selected[0]),
        redirect_attempts=0,
        answers=[],
        evaluations=[],
        status="active",
    )


async def get_question_by_id(db: AsyncSession, question_id: int) -> InterviewQuestion | None:
    return await db.get(InterviewQuestion, question_id)


def session_payload(session_state: InterviewSessionState) -> dict:
    return session_state.model_dump()


def audio_metrics_dict(metrics: object) -> dict:
    if hasattr(metrics, "__dataclass_fields__"):
        return asdict(metrics)
    if isinstance(metrics, dict):
        return metrics
    return {}
