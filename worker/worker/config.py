from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    REDIS_URL: str = "redis://redis:6379/0"
    DATABASE_URL: str = "postgresql+asyncpg://navis:changeme@postgres:5432/navis"

    class Config:
        env_file = ".env"


settings = Settings()
