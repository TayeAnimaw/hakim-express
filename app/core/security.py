import random
import string

from passlib.context import CryptContext
from app.database.database import get_redis
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def generate_random_otp(length: int = 6) -> str:
    generated_otp: str = "".join(random.choices(string.digits, k=length))
    return generated_otp

async def store_verification_code(email_or_phone: str, code: str):
    email = email_or_phone.lower().strip()
    redis = await get_redis()
    key = f"verify:{email}"
    # expires in 10 minutes
    await redis.set(key, code, ex=600)

async def verify_code(email_or_phone: str, code: str):
    email = email_or_phone.lower().strip()
    redis = await get_redis()
    key = f"verify:{email}"
    stored_code = await redis.get(key)
    
    if stored_code is None:
       return False
    
    if stored_code != code:
        return False
    
    await redis.delete(key)
    return True
# if the user verify otp successfully, we set a flag in redis to indicate that
# the email has access to change password for the next 3 minutes this make 
# security better by ensuring that only verified user can change password
async def set_email_verified(email_or_phone: str):
    email = email_or_phone.lower().strip()
    redis = await get_redis()
    key = f"email_verified:{email}"
    await redis.set(key, "true", ex=180)
# check if the email is verified by otp recently
async def verify_email_verified(email_or_phone: str) -> bool:
    email = email_or_phone.lower().strip()
    redis = await get_redis()
    key = f"email_verified:{email}"
    status = await redis.get(key)
    return status == "true"

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str):
    return pwd_context.hash(password)