import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "smart-task-reassignment-secret-key-2026")
    DATA_DIR = BASE_DIR / "data"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATA_DIR / 'workforce.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Ollama settings
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma2:latest")
    OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "4"))
    
    # Email settings (Resend / Gmail SMTP)
    EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER", "resend")
    RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
    RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "WORKFORCE-X Operations <onboarding@resend.dev>")
    GMAIL_SENDER = os.getenv("GMAIL_SENDER", "workforce.x.dispatch@gmail.com")
    GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
    DEFAULT_RECIPIENT = os.getenv("GMAIL_RECIPIENT", "manager@enterprise.com")

    # Scoring weights
    WEIGHT_SKILL = 0.40
    WEIGHT_PERFORMANCE = 0.30
    WEIGHT_WORKLOAD = 0.20
    WEIGHT_AVAILABILITY = 0.10
