import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///bugtrack.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    AI_API_KEY = os.getenv("AI_API_KEY", "")
    AI_API_URL = os.getenv("AI_API_URL", "https://api.openai.com/v1/chat/completions")
    AI_MODEL = os.getenv("AI_MODEL", "gpt-4o-mini")
