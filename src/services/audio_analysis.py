import math
import re
from dataclasses import dataclass
from pathlib import Path

from pydub import AudioSegment
from pydub.silence import detect_silence

from src.config import settings


FILLER_PATTERNS = (
    r"\bээ+\b",
    r"\bэм+\b",
    r"\bну\b",
    r"\bтипа\b",
    r"\bкак\s+бы\b",
)


@dataclass(frozen=True)
class AudioMetrics:
    duration_sec: float
    silence_ratio: float
    pause_count: int
    longest_pause_sec: float
    average_dbfs: float
    is_too_quiet: bool
    approximate_words_per_minute: float
    filler_words: int


def safe_dbfs(audio: AudioSegment) -> float:
    if math.isinf(audio.dBFS):
        return -100.0
    return float(audio.dBFS)


def silence_threshold(audio: AudioSegment) -> float:
    average_dbfs = safe_dbfs(audio)
    return average_dbfs - settings.INTERVIEW_SILENCE_RELATIVE_DB


def count_words(transcript: str) -> int:
    return len(re.findall(r"[\wА-Яа-яЁё]+", transcript, flags=re.UNICODE))


def count_filler_words(transcript: str) -> int:
    normalized = transcript.lower()
    return sum(len(re.findall(pattern, normalized, flags=re.UNICODE)) for pattern in FILLER_PATTERNS)


def words_per_minute(transcript: str, duration_sec: float) -> float:
    if duration_sec <= 0:
        return 0.0
    return round(count_words(transcript) / (duration_sec / 60), 2)


def analyze_audio_file(audio_path: Path, transcript: str = "") -> AudioMetrics:
    audio = AudioSegment.from_file(audio_path)
    duration_sec = round(len(audio) / 1000, 2)
    average_dbfs = round(safe_dbfs(audio), 2)

    silences = detect_silence(
        audio,
        min_silence_len=settings.INTERVIEW_PAUSE_MIN_MS,
        silence_thresh=silence_threshold(audio),
    )
    silence_ms = sum(end - start for start, end in silences)
    longest_pause_ms = max((end - start for start, end in silences), default=0)

    return AudioMetrics(
        duration_sec=duration_sec,
        silence_ratio=round(silence_ms / len(audio), 4) if len(audio) else 0.0,
        pause_count=len(silences),
        longest_pause_sec=round(longest_pause_ms / 1000, 2),
        average_dbfs=average_dbfs,
        is_too_quiet=average_dbfs < settings.INTERVIEW_TOO_QUIET_DBFS,
        approximate_words_per_minute=words_per_minute(transcript, duration_sec),
        filler_words=count_filler_words(transcript),
    )
