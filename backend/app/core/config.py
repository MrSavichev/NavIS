from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://navis:changeme@postgres:5432/navis"
    REDIS_URL: str = "redis://redis:6379/0"
    SECRET_KEY: str = "change-this-secret-key"
    DEBUG: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
