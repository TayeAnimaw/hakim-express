# app/database/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from app.core.config import settings  # Import settings
# import redis
from redis import asyncio as aioredis

# Load environment variables from .env file
load_dotenv()

# Use DATABASE_URL from settings
DATABASE_URL = settings.DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
redis_client = None
# Define the get_db function
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
# initialize redis connection pool
async def init_redis():
    global redis_client
    REDIS_HOST = settings.REDIS_HOST
    REDIS_PORT = int(settings.REDIS_PORT)
    REDIS_USER = settings.REDIS_USER
    REDIS_PASSWORD = settings.REDIS_PASSWORD
    if redis_client is None:
        redis_client = aioredis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            username=REDIS_USER,
            password=REDIS_PASSWORD,
            decode_responses=True,
        )
        await redis_client.ping()

# get redis connection
async def get_redis() -> aioredis.Redis:
    if redis_client is None:
        raise Exception("Redis client not initialized")
    return redis_client