import os 
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv("/Users/masterpo/Desktop/TheThinker/backend/.env")

class Settings():
    # DexScreener
    DEX_URL: str = os.getenv("DEX_URL")
    ENDPOINTS: list = os.getenv("ENDPOINTS", "").split(',')

    # Filepaths
    RAW_DATA_FILEPATH: str = os.getenv("RAW_DATA_FILEPATH")
    CLEAN_DATA_FILEPATH: str = os.getenv("CLEAN_DATA_FILEPATH")

    # WhaleTracker
    MIN_INVESTMENT: int = os.getenv("MIN_INVESTMENT")
    ALERT_AMOUNT: int = os.getenv("ALERT_AMOUNT")
    SOLANA_RPC: str = os.getenv("SOLANA_RPC")
    HELIUS_API_KEY: str = os.getenv("HELIUS_API_KEY")

    # Telegram bot API
    BOT_TOKEN: str = os.getenv("BOT_TOKEN")


settings = Settings()
