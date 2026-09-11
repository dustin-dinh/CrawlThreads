from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]


class AppConfig(BaseSettings):
    app_name: str = "Tôi Kể Chuyện Lạ — Story Miner"
    environment: str = "development"
    database_url: str = f"sqlite:///{(ROOT_DIR / 'data' / 'story_miner.db').as_posix()}"
    frontend_dist: str = str(ROOT_DIR / "frontend" / "dist")
    log_file: str = str(ROOT_DIR / "logs" / "app.log")
    threads_access_token: str = ""
    threads_app_id: str = ""
    threads_app_secret: str = ""
    threads_api_base: str = "https://graph.threads.net/v1.0"
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "windows:story-miner:1.0 (local research tool)"
    ai_enabled: bool = False
    ai_base_url: str = "https://api.openai.com/v1"
    ai_api_key: str = ""
    ai_model: str = "gpt-4.1-mini"
    ollama_base_url: str = "http://127.0.0.1:11434/v1"
    duplicate_similarity_threshold: float = 0.88
    request_timeout_seconds: float = 20.0
    max_retries: int = 3

    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_config() -> AppConfig:
    return AppConfig()

