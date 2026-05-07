from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/playlist_ai"
    SECRET_KEY: str = "your-secret-key"
    AI_API_KEY: str = "your-ai-api-key"


settings = Settings()
