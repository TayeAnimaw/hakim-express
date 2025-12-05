# app/core/config.py

import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Hakim Express"
    VERSION: str = "1.0"

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://hakim_express_user:i3RUSUmRAqcgosUyQI3DanOuiXEXJxGv@dpg-d4lut58gjchc73aulttg-a.oregon-postgres.render.com:5432/hakim_express_v62w?sslmode=require"
    )

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "4f66b8a5-97b1-44e0-91c1-1b5601293783#lkl*do5fb87md@8jfi3$")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    # Mail Configuration
    MAIL_MAILER: str = os.getenv("MAIL_MAILER", "smtp")
    MAIL_HOST: str | None = os.getenv("MAIL_HOST")
    MAIL_PORT: int = int(os.getenv("MAIL_PORT", 587))
    MAIL_USERNAME: str | None = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD: str | None = os.getenv("MAIL_PASSWORD")
    MAIL_ENCRYPTION: str = os.getenv("MAIL_ENCRYPTION", "ssl")
    MAIL_FROM_ADDRESS: str | None = os.getenv("MAIL_FROM_ADDRESS")
    MAIL_FROM_NAME: str | None = os.getenv("MAIL_FROM_NAME")

    # Stripe
    STRIPE_SECRET_KEY: str | None = os.getenv("STRIPE_SECRET_KEY")
    STRIPE_PUBLISHABLE_KEY: str | None = os.getenv("STRIPE_PUBLISHABLE_KEY")

    # Redis
    REDIS_HOST: str | None = os.getenv("REDIS_HOST")
    REDIS_PORT: int | None = int(os.getenv("REDIS_PORT", 6379))
    REDIS_USER: str | None = os.getenv("REDIS_USER")
    REDIS_PASSWORD: str | None = os.getenv("REDIS_PASSWORD")

    # Bank of Abyssinia API
    BOA_BASE_URL: str = os.getenv("BOA_BASE_URL", "https://boapibeta.bankofabyssinia.com/remittance/hakimRemit")
    BOA_CLIENT_ID: str = os.getenv("BOA_CLIENT_ID", "hakimRemit_staging")
    BOA_CLIENT_SECRET: str | None = os.getenv("BOA_CLIENT_SECRET")
    BOA_REFRESH_TOKEN: str | None = os.getenv("BOA_REFRESH_TOKEN")
    BOA_X_API_KEY: str | None = os.getenv("BOA_X_API_KEY")
    BOA_AUTH_PREFIX: str = os.getenv("BOA_AUTH_PREFIX", "")
    BOA_TOKEN_FILE: str = os.getenv("BOA_TOKEN_FILE", "./boa_token.json")

    # Pydantic v2 config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


# Initialize
settings = Settings()
