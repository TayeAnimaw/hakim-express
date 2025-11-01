# File: app/security.py
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials,OAuth2PasswordBearer
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Request
from app.core.config import settings
from passlib.context import CryptContext
from datetime import datetime, timedelta
from app.models.users import User
from app.schemas.users import TokenData
from app.database.database import get_db
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.users import User, Role


from app.database.database import get_db
# Password utilities
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# JWT utilities
def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        print(f"Decoded payload: {payload}")
        return payload  # Payload should have a 'sub' field which is the user_id
    except JWTError:
        raise HTTPException(
            status_code=403,
            detail="Could not validate credentials",
        )
def create_refresh_token(data: dict, expires_delta: timedelta = timedelta(days=7)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
def get_current_user(db: Session = Depends(get_db), token: dict = Depends(verify_access_token)):
    print(f"Decoded token: {token}")  # Print the decoded token to check the payload
    user_id = token.get("sub")
    print(f"Extracted user_id from token: {user_id}")  # Print user_id
    if user_id is None:
        raise HTTPException(status_code=403, detail="Invalid token: no user_id")
    try:
        user_id = int(user_id)
    except ValueError:
        raise HTTPException(status_code=403, detail="Invalid token: user_id not integer")
    user = db.query(User).filter(User.user_id == user_id).first()
    print(f"Fetched user: {user}")  # Print the fetched user
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    print(user.role,"==============")
    return user

# Custom JWTBearer for security
class JWTBearer(HTTPBearer):
    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        token = credentials.credentials if credentials else request.query_params.get('token')
        if not token:
            raise HTTPException(
                status_code=403,
                detail="Invalid or expired token",
            )
        # Strip surrounding quotes if present
        token = token.strip('"')
        return verify_access_token(token)
def authenticate_user(db: Session, login_id: str, password: str):
    # Try to find user by email or phone
    user = db.query(User).filter(
        (User.email == login_id) | (User.phone == login_id)
    ).first()

    if not user:
        print("User not found")
        return False
    if not verify_password(password, user.password):
        print("Password verification failed")        
        return False
    return user
def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != Role.admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

def check_permission(permission: str):
    async def permission_checker(current_user: User = Depends(get_current_user)):
        if current_user.role != Role.admin:
            raise HTTPException(status_code=403, detail="Admin access required")
            
        # Check if admin has the specific permission
        if not current_user.admin_role or \
           not any(p.permission == permission for p in current_user.admin_role.permissions):
            raise HTTPException(status_code=403, detail=f"Missing permission: {permission}")
        return current_user  # Return the user if checks pass
            
    return permission_checker  # Return the inner function, not Depends()
