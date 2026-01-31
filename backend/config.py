from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """應用程式設定"""

    # 應用資訊
    app_name: str = "Sukuyodo API"
    app_version: str = "1.0.0"
    debug: bool = False

    # 資料庫
    database_url: str = ""

    # CORS
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "https://sukuyodo.vercel.app",
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
