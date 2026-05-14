import os
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = Path("/tmp") if os.getenv("VERCEL") else ROOT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)


class Settings(BaseSettings):
    app_name: str = "StockSense AI Pro"
    app_version: str = "1.0.0"
    database_url: str = f"sqlite:///{DATA_DIR / 'stocksense.db'}"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    cache_ttl_seconds: int = 300
    default_history_period: str = "1y"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
