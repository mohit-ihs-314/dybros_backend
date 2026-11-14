
import os
from pathlib import Path
from dotenv import load_dotenv


# --------------------------------------------------
# ENVIRONMENT CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_FILE)


class Config:

    # Application
    APP_NAME = os.getenv("APP_NAME", "DYABROS")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    PORT = int(os.getenv("PORT", 5000))

    # Security
    SECRET_KEY = os.getenv("SECRET_KEY")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

    # MongoDB
    MONGO_URI = os.getenv("MONGO_URI")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "dyabros_db")

    # Frontend CORS
    FRONTEND_ORIGINS = [
        "https://mohit-ihs-314.github.io",
        "http://localhost:8443",
        "http://127.0.0.1:8443",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    @classmethod
    def validate(cls):

        required = [
            "SECRET_KEY",
            "JWT_SECRET_KEY",
            "MONGO_URI",
        ]

        missing = [
            key for key in required
            if not getattr(cls, key)
        ]

        if missing:
            raise ValueError(
                "Missing required environment variables: "
                + ", ".join(missing)
            )

        if not cls.MONGO_DB_NAME:
            raise ValueError("MONGO_DB_NAME cannot be empty.")

        if not cls.FRONTEND_ORIGINS:
            raise ValueError("At least one frontend origin is required.")
