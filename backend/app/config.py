from pydantic import BaseSettings

class Settings(BaseSettings):
    DEX_URL: str

    class Config:
        env_file = ".env"  # Автозагрузка переменных окружения

settings = Settings()