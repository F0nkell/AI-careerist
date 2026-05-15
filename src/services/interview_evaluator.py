import json
from typing import Any

from src.config import settings
from src.models.interview_question import InterviewQuestion
from src.services.audio_analysis import AudioMetrics
from src.services.transcription import get_vsegpt_client


EVALUATION_SYSTEM_PROMPT = """
Ты оцениваешь ответ кандидата на backend-интервью по Python.
Верни только валидный JSON без markdown и пояснений вокруг.

Правила:
- Если ответ не по теме вопроса, не оценивай по ощущениям.
- Если ответ не по теме и redirect_attempts < max_redirects, попроси вернуться к тому же вопросу.
- Если ответ не по теме после max_redirects, поставь coverage_percent=0.
- Если ответ частично по теме, оцени coverage_percent только по весам key_points.
- Не раскрывай полный expected_answer в обратной связи.
- Обратная связь должна быть прямой, короткой и полезной.
""".strip()


FINAL_REPORT_SYSTEM_PROMPT = """
Ты подводишь итог backend-интервью по Python.
Верни только валидный JSON без markdown и пояснений вокруг.
Итог должен содержать estimated_level, total_score, per_topic_scores, strengths,
weak_topics, missing_topics и recommended_study_plan.
Не раскрывай полные эталонные ответы.
""".strip()


DEFAULT_EVALUATION: dict[str, Any] = {
    "on_topic": False,
    "coverage_percent": 0,
    "covered_points": [],
    "missing_points": [],
    "red_flags_seen": [],
    "should_redirect": False,
    "redirect_message": "",
    "should_follow_up": False,
    "follow_up_question": "",
    "final_feedback_to_user": "",
    "score_reason": "",
}


def public_key_point_titles(question: InterviewQuestion) -> list[str]:
    return [str(point.get("title", "")) for point in question.key_points if point.get("title")]


def question_prompt_payload(question: InterviewQuestion) -> dict[str, Any]:
    return {
        "id": question.id,
        "profession": question.profession,
        "language": question.language,
        "competency": question.competency,
        "level": question.level,
        "difficulty": question.difficulty,
        "question_text": question.question_text,
        "expected_answer": question.expected_answer,
        "key_points": question.key_points,
        "red_flags": question.red_flags,
        "follow_ups": question.follow_ups,
        "evaluation_rubric": question.evaluation_rubric,
    }


def audio_metrics_payload(audio_metrics: AudioMetrics | dict[str, Any]) -> dict[str, Any]:
    if isinstance(audio_metrics, AudioMetrics):
        return {
            "duration_sec": audio_metrics.duration_sec,
            "silence_ratio": audio_metrics.silence_ratio,
            "pause_count": audio_metrics.pause_count,
            "longest_pause_sec": audio_metrics.longest_pause_sec,
            "average_dbfs": audio_metrics.average_dbfs,
            "is_too_quiet": audio_metrics.is_too_quiet,
            "approximate_words_per_minute": audio_metrics.approximate_words_per_minute,
            "filler_words": audio_metrics.filler_words,
        }
    return dict(audio_metrics)


def extract_json_object(content: str) -> dict[str, Any]:
    stripped = content.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        stripped = stripped.removeprefix("json").strip()

    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        parsed = json.loads(stripped[start : end + 1])

    if not isinstance(parsed, dict):
        raise ValueError("LLM response must be a JSON object")
    return parsed


def clamp_percent(value: object) -> int:
    if not isinstance(value, (int, float)):
        return 0
    return max(0, min(100, int(round(value))))


def normalize_evaluation(
    raw_evaluation: dict[str, Any],
    question: InterviewQuestion,
    redirect_attempts: int,
) -> dict[str, Any]:
    normalized = DEFAULT_EVALUATION | raw_evaluation
    normalized["on_topic"] = bool(normalized.get("on_topic"))
    normalized["coverage_percent"] = clamp_percent(normalized.get("coverage_percent"))

    if not normalized["on_topic"]:
        normalized["coverage_percent"] = 0
        normalized["covered_points"] = []
        normalized["missing_points"] = public_key_point_titles(question)
        normalized["should_follow_up"] = False
        normalized["follow_up_question"] = ""

        if redirect_attempts < settings.INTERVIEW_MAX_REDIRECTS:
            normalized["should_redirect"] = True
            if not normalized.get("redirect_message"):
                normalized["redirect_message"] = "Вернитесь к вопросу и ответьте по сути. Сейчас ответ ушел в сторону."
            normalized["final_feedback_to_user"] = normalized["redirect_message"]
        else:
            normalized["should_redirect"] = False
            normalized["redirect_message"] = ""
            normalized["final_feedback_to_user"] = (
                "Ответ снова не относится к вопросу. Этот вопрос засчитан как 0, переходим дальше."
            )
        return normalized

    normalized["should_redirect"] = False
    normalized["redirect_message"] = ""
    if not normalized.get("final_feedback_to_user"):
        normalized["final_feedback_to_user"] = "Ответ принят. Продолжайте держать фокус на ключевых технических деталях."
    return normalized


async def request_json_from_llm(system_prompt: str, payload: dict[str, Any], max_tokens: int) -> dict[str, Any]:
    client = get_vsegpt_client()
    response = await client.chat.completions.create(
        model=settings.interview_chat_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ],
        temperature=settings.INTERVIEW_LLM_TEMPERATURE,
        max_tokens=max_tokens,
        extra_headers={"HTTP-Referer": "https://t.me/ResumeKillerBot", "X-Title": "ResumeKiller"},
    )
    content = response.choices[0].message.content or "{}"
    return extract_json_object(content)


async def evaluate_answer(
    question: InterviewQuestion,
    transcript: str,
    audio_metrics: AudioMetrics | dict[str, Any],
    redirect_attempts: int,
    prior_context: list[dict[str, Any]],
) -> dict[str, Any]:
    payload = {
        "question": question_prompt_payload(question),
        "transcript": transcript,
        "audio_metrics": audio_metrics_payload(audio_metrics),
        "redirect_attempts": redirect_attempts,
        "max_redirects": settings.INTERVIEW_MAX_REDIRECTS,
        "prior_context": prior_context,
        "required_json_schema": DEFAULT_EVALUATION,
    }
    raw_evaluation = await request_json_from_llm(
        EVALUATION_SYSTEM_PROMPT,
        payload,
        settings.INTERVIEW_EVALUATION_MAX_TOKENS,
    )
    return normalize_evaluation(raw_evaluation, question, redirect_attempts)


def deterministic_report(evaluations: list[dict[str, Any]]) -> dict[str, Any]:
    scored = [item for item in evaluations if isinstance(item.get("coverage_percent"), (int, float))]
    total_score = round(sum(float(item["coverage_percent"]) for item in scored) / len(scored), 2) if scored else 0.0

    per_topic: dict[str, list[float]] = {}
    missing_topics: set[str] = set()
    for item in scored:
        competency = str(item.get("competency", "unknown"))
        per_topic.setdefault(competency, []).append(float(item["coverage_percent"]))
        if float(item["coverage_percent"]) < 60:
            missing_topics.add(competency)

    if total_score >= 85:
        estimated_level = "senior"
    elif total_score >= 65:
        estimated_level = "middle"
    else:
        estimated_level = "junior"

    return {
        "estimated_level": estimated_level,
        "total_score": total_score,
        "per_topic_scores": {
            topic: round(sum(scores) / len(scores), 2)
            for topic, scores in sorted(per_topic.items())
        },
        "strengths": [
            topic for topic, scores in sorted(per_topic.items()) if sum(scores) / len(scores) >= 75
        ],
        "weak_topics": sorted(missing_topics),
        "missing_topics": sorted(missing_topics),
        "recommended_study_plan": [
            "Повторить темы с coverage ниже 60%.",
            "Практиковать короткие структурированные ответы: определение, trade-offs, пример из backend.",
            "Разобрать типовые production-сценарии по FastAPI, PostgreSQL, async и безопасности.",
        ],
    }


async def build_final_report(session_summary: dict[str, Any]) -> dict[str, Any]:
    try:
        return await request_json_from_llm(
            FINAL_REPORT_SYSTEM_PROMPT,
            session_summary,
            settings.INTERVIEW_REPORT_MAX_TOKENS,
        )
    except Exception:
        return deterministic_report(session_summary.get("evaluations", []))
