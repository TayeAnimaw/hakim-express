import random
import re
import string
from slowapi import Limiter
from slowapi.util import get_remote_address
from passlib.context import CryptContext
from app.database.database import get_redis
import stripe
from .config import *
import stripe
from fastapi import HTTPException
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["30/minute"]  # Allows 60 requests per minute globally per IP
)

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
    print(stored_code, code)
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
    await redis.set(key, "true", ex=600)
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

  # assuming you have your Stripe key here

stripe.api_key = settings.STRIPE_SECRET_KEY  # test secret key

def create_stripe_payment_method(email: str = "dev@example.com") -> str:
    """
    Create a Stripe customer (if needed), create a PaymentMethod using a test token,
    attach it to the customer, and return the PaymentMethod ID.
    """
    try:
        # Create a test customer
        customer = stripe.Customer.create(email=email, source="tok_visa")

        # Create a PaymentMethod using test token
        pm = stripe.PaymentMethod.create(type="card", card={"token": "tok_visa"})
        pm_id = pm.id

        # Attach PaymentMethod to the customer
        stripe.PaymentMethod.attach(pm_id, customer=customer.id)
        return pm_id

    except stripe.error.StripeError as e:
        return None

def is_valid_phone_number(phone: str) -> bool:
    """
    Check if a phone number is valid with country code (E.164 format).
    Example valid: +251912345678, +491234567890
    """
    pattern = r'^\+[1-9]\d{7,14}$'
    return bool(re.fullmatch(pattern, phone))


async def check_rate_limit(email_or_phone: str, action: str, limit: int = 5, window: int = 600):
    
    email = email_or_phone.lower().strip()
    redis = await get_redis()
    key = f"rate_limit:{action}:{email}"
    
    current_attempts = await redis.get(key)
    
    if current_attempts and int(current_attempts) >= limit:
        return False  # Limit exceeded
    await increment_rate_limit(
        email_or_phone=email_or_phone,
        action=action,
        window=window
    )
    
    return True

async def increment_rate_limit(email_or_phone: str, action: str, window: int = 600):
    """Increments the attempt counter for a specific user action."""
    email = email_or_phone.lower().strip()
    redis = await get_redis()
    key = f"rate_limit:{action}:{email}"
 
    new_val = await redis.incr(key)
    if new_val == 1:
        await redis.expire(key, window)
        
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # HSTS: enforce HTTPS for 1 year
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        # Clickjacking protection
        response.headers["X-Frame-Options"] = "DENY"

        # Prevent MIME-type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Content Security Policy
        # Use a looser CSP for development (Swagger) and strict for production
        if os.getenv("ENV", "development") == "development":
            # Allow Swagger resources
            csp = (
                "default-src 'self'; "
                "script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
                "style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
                "img-src 'self' https://fastapi.tiangolo.com;"
            )
        else:
            # Strict CSP for production
            csp = (
                "default-src 'self'; "
                "frame-ancestors 'none'; "
                "script-src 'self'; "
                "style-src 'self'; "
                "img-src 'self';"
            )

        response.headers["Content-Security-Policy"] = csp.strip()

        # Referrer policy
        response.headers["Referrer-Policy"] = "no-referrer"

        # Permissions policy (modern replacement for Feature-Policy)
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"

        # Cross-Origin policies
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"

        return response