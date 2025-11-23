import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Конфигурация приложения"""
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/codeforces_db")
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    CODEFORCES_URL = "https://codeforces.com/api/problemset.problems"
    UPDATE_INTERVAL_HOURS = 1

    DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
    DATABASE_PORT = os.getenv("DATABASE_PORT", "5432")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "codeforces_db")
    DATABASE_USER = os.getenv("DATABASE_USER", "user")
    DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "password")


config = Config()
