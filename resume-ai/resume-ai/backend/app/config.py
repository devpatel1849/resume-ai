import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings:
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_ENV = os.getenv("PINECONE_ENV")
    PINECONE_INDEX = os.getenv("PINECONE_INDEX")

    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    AUTH_SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "change-this-secret-key")
    AUTH_TOKEN_EXPIRE_MINUTES = int(os.getenv("AUTH_TOKEN_EXPIRE_MINUTES", "120"))

settings = Settings()