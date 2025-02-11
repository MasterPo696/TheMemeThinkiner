from pydantic import BaseSettings

class Settings(BaseSettings):
    DEX_URL: str
    BOT_TOKEN: str

    class Config:
        env_file = ".env"  # Автозагрузка переменных окружения

settings = Settings()