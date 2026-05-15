from dataclasses import dataclass
from pathlib import Path

from openai import AsyncOpenAI

from src.config import settings


VERBATIM_TRANSCRIPTION_PROMPT = (
    "Транскрибируй речь дословно на русском языке. "
    "Сохраняй слова-паразиты и заполнители пауз: ээ, эм, ну, типа, как бы. "
    "Сохраняй повторы и незаконченные фразы, когда это возможно. "
    "Не превращай речь в отредактированный литературный текст."
)


@dataclass(frozen=True)
class TranscriptionResult:
    transcript: str
    provider: str
    model: str
    duration: float | None = None


def get_vsegpt_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=settings.vsegpt_api_key,
        base_url=settings.vsegpt_base_url,
    )


def extract_transcript_text(response: object) -> str:
    text = getattr(response, "text", None)
    if isinstance(text, str):
        return text.strip()
    if isinstance(response, dict) and isinstance(response.get("text"), str):
        return response["text"].strip()
    return ""


def extract_duration(response: object) -> float | None:
    duration = getattr(response, "duration", None)
    if isinstance(duration, (int, float)):
        return float(duration)
    if isinstance(response, dict) and isinstance(response.get("duration"), (int, float)):
        return float(response["duration"])
    return None


async def transcribe_audio_file(audio_path: Path) -> TranscriptionResult:
    client = get_vsegpt_client()
    model = settings.interview_stt_model

    with audio_path.open("rb") as audio_file:
        response = await client.audio.transcriptions.create(
            model=model,
            file=audio_file,
            language="ru",
            prompt=VERBATIM_TRANSCRIPTION_PROMPT,
        )

    return TranscriptionResult(
        transcript=extract_transcript_text(response),
        provider="vsegpt",
        model=model,
        duration=extract_duration(response),
    )
