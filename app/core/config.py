# app/core/config.py

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    PROJECT_NAME: str = "Hakim Express"
    VERSION: str = "1.0"    
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://hakim_express_user:mXJK81GKUkBxMb3UBNUpp1CMLkixtutd@dpg-d40pj6k9c44c73c9qb20-a.oregon-postgres.render.com/hakim_express_10js")
    # Secret Key for JWT Token and other sensitive operations
    SECRET_KEY: str = os.getenv("SECRET_KEY", "4f66b8a5-97b1-44e0-91c1-1b5601293783#lkl*do5fb87md@8jfi3$")
    
    # JWT Token algorithm and expiry time settings
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    MAIL_MAILER: str = os.getenv("MAIL_MAILER", "smtp")
    MAIL_HOST: str = os.getenv("MAIL_HOST")
    MAIL_PORT: int = int(os.getenv("MAIL_PORT", 587))
    MAIL_USERNAME: str = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD: str = os.getenv("MAIL_PASSWORD")
    MAIL_ENCRYPTION: str = os.getenv("MAIL_ENCRYPTION", "ssl")
    MAIL_FROM_ADDRESS: str = os.getenv("MAIL_FROM_ADDRESS")
    MAIL_FROM_NAME: str = os.getenv("MAIL_FROM_NAME")
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY")
    STRIPE_PUBLISHABLE_KEY: str = os.getenv("STRIPE_PUBLISHABLE_KEY")
    
    # Bank of Abyssinia API Configuration
    BOA_BASE_URL: str = os.getenv("BOA_BASE_URL", "https://boapibeta.bankofabyssinia.com/remittance/hakimRemit")
    BOA_CLIENT_ID: str = os.getenv("BOA_CLIENT_ID", "hakimRemit_staging")
    BOA_CLIENT_SECRET: str = os.getenv("BOA_CLIENT_SECRET")
    BOA_REFRESH_TOKEN: str = os.getenv("BOA_REFRESH_TOKEN")
    BOA_X_API_KEY: str = os.getenv("BOA_X_API_KEY")

    # Optional: Authorization header prefix (empty string "" or "Bearer ")
    BOA_AUTH_PREFIX: str = os.getenv("BOA_AUTH_PREFIX", "")

    # Optional: Token cache file
    BOA_TOKEN_FILE: str = os.getenv("BOA_TOKEN_FILE", "./boa_token.json")

# Initialize settings instance
settings = Settings()
