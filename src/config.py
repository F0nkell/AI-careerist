from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    BOT_TOKEN: str
    API_PORT: int = 8000
    SECRET_KEY: str

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    
    # VseGPT is OpenAI-compatible. OPENROUTER_* stays as a compatibility
    # fallback for existing deployments that already use those names.
    VSEGPT_API_KEY: str | None = None
    VSEGPT_BASE_URL: str | None = None
    OPENROUTER_API_KEY: str | None = None
    OPENROUTER_BASE_URL: str = "https://api.vsegpt.ru/v1"
    OPENROUTER_CHAT_MODEL: str = "google/gemini-2.5-flash-lite"
    OPENROUTER_STT_MODEL: str = "stt-openai/whisper-v3-turbo"

    INTERVIEW_EVALUATION_MODEL: str | None = None
    INTERVIEW_STT_MODEL: str | None = None
    INTERVIEW_EVALUATION_MAX_TOKENS: int = 1200
    INTERVIEW_REPORT_MAX_TOKENS: int = 1200
    INTERVIEW_LLM_TEMPERATURE: float = 0.2
    INTERVIEW_QUESTION_COUNT: int = 7
    INTERVIEW_MAX_REDIRECTS: int = 2
    INTERVIEW_PAUSE_MIN_MS: int = 700
    INTERVIEW_TOO_QUIET_DBFS: float = -35.0
    INTERVIEW_SILENCE_RELATIVE_DB: float = 16.0
    INTERVIEW_DEFAULT_PROFESSION: str = "backend"
    INTERVIEW_DEFAULT_LANGUAGE: str = "python"
    INTERVIEW_TTS_VOICE: str = "ru-RU-DmitryNeural"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def vsegpt_api_key(self) -> str:
        api_key = self.VSEGPT_API_KEY or self.OPENROUTER_API_KEY
        if not api_key:
            raise ValueError("VSEGPT_API_KEY or OPENROUTER_API_KEY must be configured")
        return api_key

    @property
    def vsegpt_base_url(self) -> str:
        return self.VSEGPT_BASE_URL or self.OPENROUTER_BASE_URL

    @property
    def interview_chat_model(self) -> str:
        return self.INTERVIEW_EVALUATION_MODEL or self.OPENROUTER_CHAT_MODEL

    @property
    def interview_stt_model(self) -> str:
        return self.INTERVIEW_STT_MODEL or self.OPENROUTER_STT_MODEL

settings = Settings()
