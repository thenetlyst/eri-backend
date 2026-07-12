import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        os.getenv("DATABASE_URL_LOCAL")
    )

    RANKING_ADMIN_KEY: str = os.getenv("RANKING_ADMIN_KEY", "")

    CORS_ORIGINS: list[str] = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173"
    ).split(",")


settings = Settings()