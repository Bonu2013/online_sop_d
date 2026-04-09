from dataclasses import dataclass
from dotenv import load_dotenv
import os

load_dotenv()

@dataclass
class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN")

    # Railway'da ulanish uchun eng muhimi - DATABASE_URL
    # Agar u bo'lmasa, alohida o'zgaruvchilarga murojaat qilamiz
    DATABASE_URL: str = os.getenv("DATABASE_URL")

    # Alohida o'zgaruvchilar (Lokal uchun)
    # get(..., "default_qiymat") xatolikni oldini oladi
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", 5432))
    DB_NAME: str = os.getenv("DB_NAME", "postgres")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "password")

config = Config()