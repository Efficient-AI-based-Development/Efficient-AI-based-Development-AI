# app/core/config.py

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


# 설정
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )
    APP_NAME: str = "Efficient-AI-Dev System"
    API_V1_STR: str = "/api/v1"
    UPSTAGE_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: str = "1521"
    DB_SERVICE_NAME: str
    LLM_MODEL_SOLAR: str = "solar-pro2"
    LLM_MODEL_PM: str = "solar-pro2"
    LLM_MODEL_TASK_AI: str = "solar-pro2"
    LLM_MODEL_WRITER: str = "solar-pro2"
    LLM_MODEL_AUDITOR: str = "solar-pro2"
    LLM_MODEL_DECOMPOSER: str = "solar-pro2"

    @property
    def DATABASE_URL(self) -> str:
        return f"oracle+oracledb://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/?service_name={self.DB_SERVICE_NAME}"


# 설정 객체 캐싱 반환
@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
