from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/playlist_ai"
    SECRET_KEY: str = "your-secret-key"
    AI_API_KEY: str = "your-ai-api-key"
    AI_API_URL: str = "https://api.example.com"
    MUSIC_API_KEY: str = "your-music-api-key"
    MUSIC_API_URL: str = "https://api.example.com"


settings = Settings()
