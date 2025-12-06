from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Formatter"
    PROJECT_VERSION: str = "0.1.0"
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/formatter"
    REDIS_URL: str = "redis://redis:6379/0"
    SECRET_KEY: str = "changethis"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        case_sensitive = True

settings = Settings()
