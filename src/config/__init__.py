"""Cấu hình tập trung bằng Pydantic Settings."""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5434
    POSTGRES_DB: str = "it-recommend-system"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    DATABASE_URL: str | None = None
    VECTOR_DIM: int = 384

    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: list[str] = ["*"]

    MAX_UPLOAD_MB: int = 5
    MAX_PAGES: int = 10

    MODEL_NAME: str = "all-MiniLM-L6-v2"

    TOP_K: int = 10
    JD_WORDS_PER_CHUNK: int = 120
    SCORE_TOP_K_REQS: int = 3
    MATCH_RECENCY_DAYS: int = 21
    RECENCY_SCORE_FLOOR: float = 0.7

    MISSING_GRACE_DAYS: int = 7
    EXPIRE_AFTER_DAYS: int = 30

    BREAKPOINT_PERCENTILE: float = 70.0
    MIN_DISTANCE: float = 0.15
    MIN_CHARS: int = 120
    MAX_CHARS: int = 500
    WINDOW: int = 1

    IT_SCORE_THRESHOLD: int = 3

    ARBEITNOW_URL: str = "https://www.arbeitnow.com/api/job-board-api"
    ARBEITNOW_TIMEOUT: int = 20
    JOBICY_URL: str = "https://jobicy.com/api/v2/remote-jobs"
    JOBICY_TIMEOUT: int = 20
    JOBICY_COUNT: int = 50

    UPDATE_TOKEN: str = ""
    PAGE_SIZE: int = 9


settings = Settings()
