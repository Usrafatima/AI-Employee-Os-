from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Employee OS"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # CORS Configuration
    CORS_ORIGINS: List[Union[str, AnyHttpUrl]] = ["http://localhost:3000"]

    @field_validator("CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Database
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/ai_employee_os"

    # Security
    SECRET_KEY: str = "change_this_to_a_secure_random_secret_key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # OpenAI / AI Orchestration Settings
   # OpenAI / AI Orchestration Settings
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"

    # OpenAI / AI Orchestration Settings
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"

    # Email Integration (SMTP) - Communication Hub
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_TLS: bool = True
    EMAILS_FROM_EMAIL: str = ""
    EMAILS_FROM_NAME: str = "AI Employee OS"

    # WhatsApp Integration - Communication Hub (simulated until configured)
    WHATSAPP_API_TOKEN: str = ""

    model_config = SettingsConfigDict(

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
