from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[3]  # project root


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")

    results_dir: Path = BASE_DIR / "extraction_results"

    # PaddleOCR scores are 0-1, Tesseract's are 0-100
    paddle_low_conf_threshold: float = 0.80
    tesseract_low_conf_threshold: int = 80
    tesseract_psm: int = 6

    gemini_api_key: str
    gemini_model: str = "gemini-3.8-flash"
    gemini_max_upload_mb: int = 10  # Gemini's inline request limit is ~20 MB total

    groq_api_key: str
    groq_max_upload_mb: int = 3
    groq_model: str = "qwen/qwen3.8-27b"
    groq_base_url: str

    markdown_results_dir: Path = BASE_DIR / "extraction_results" / "markdown"

    max_markdown_mb: int = 1  # ~1 MB of text is roughly 250k tokens, well inside Gemini's context

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
 
    @property
    def DATABASE_URL(self) -> str:
        # async driver, used by the FastAPI app and by Alembic's async env.py
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    @property
    def max_markdown_bytes(self) -> int:
        return self.max_markdown_mb * 1024 * 1024

    @property
    def paddleocr_results_dir(self) -> Path:
        return self.results_dir / "paddleocr"

    @property
    def tesseract_results_dir(self) -> Path:
        return self.results_dir / "tesseract"

    @property
    def gemini_max_upload_bytes(self) -> int:
        return self.gemini_max_upload_mb * 1024 * 1024

    @property
    def groq_max_upload_bytes(self) -> int:
        return self.groq_max_upload_mb * 1024 * 1024


settings = Settings()