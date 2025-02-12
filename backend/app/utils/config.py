import os 

class Settings():
    DEX_URL: str = os.getenv("DEX_URL")
    BOT_TOKEN: str = os.getenv("BOT_TOKEN")

    class Config:
        env_file = "backend/.env"  # Автозагрузка переменных окружения

settings = Settings()