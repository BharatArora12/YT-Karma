from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App Information
    APP_NAME: str = "YT Shorts Management System"
    VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Google Gemini API
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # Whisper Settings
    WHISPER_MODEL_SIZE: str = "base"
    WHISPER_DEVICE: str = "cpu"
    WHISPER_COMPUTE_TYPE: str = "int8"

    # Google OAuth 2.0 Settings (YouTube Upload)
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/google/callback"
    GOOGLE_CLIENT_SECRETS_FILE: str = "client_secrets.json"

    # FFmpeg Settings
    FFMPEG_PATH: str = ""
    FFPROBE_PATH: str = ""

    # Storage Settings
    STORAGE_DIR: str = "./storage"

    # Network / CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def base_storage_path(self) -> Path:
        p = Path(self.STORAGE_DIR).resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def downloads_dir(self) -> Path:
        p = self.base_storage_path / "downloads"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def transcripts_dir(self) -> Path:
        p = self.base_storage_path / "transcripts"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def subtitles_dir(self) -> Path:
        p = self.base_storage_path / "subtitles"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def shorts_dir(self) -> Path:
        p = self.base_storage_path / "output_shorts"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def tokens_dir(self) -> Path:
        p = self.base_storage_path / "tokens"
        p.mkdir(parents=True, exist_ok=True)
        return p


settings = Settings()
