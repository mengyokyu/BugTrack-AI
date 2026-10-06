import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///bugtrack.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    AI_API_KEY = os.getenv("AI_API_KEY", "")
    AI_API_URL = os.getenv("AI_API_URL", "https://api.openai.com/v1/chat/completions")
    AI_MODEL = os.getenv("AI_MODEL", "gpt-4o-mini")
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    PERMANENT_SESSION_LIFETIME = 3600
    MAX_CONTENT_LENGTH = 64 * 1024
    PAGE_SIZE = 20


class TestConfig(Config):
    SECRET_KEY = "test-only-secret"
    TESTING = True
    WTF_CSRF_ENABLED = False
