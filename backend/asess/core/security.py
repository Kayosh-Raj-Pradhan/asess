from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import os

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key_here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

def hash_password(password: str) -> str:
    # Bcrypt has a 72-byte limit, truncate to be safe
    password = password[:72]
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Bcrypt has a 72-byte limit, truncate to be safe
    plain_password = plain_password[:72]
    return pwd_context.verify(plain_password, hashed_password)

def create_tokens(subject: str, role: str):
    # Access Token
    access_expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_payload = {"sub": subject, "role": role, "exp": access_expire}
    access_token = jwt.encode(access_payload, SECRET_KEY, algorithm=ALGORITHM)
    
    # Refresh Token
    refresh_expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_payload = {"sub": subject, "exp": refresh_expire, "scope": "refresh"}
    refresh_token = jwt.encode(refresh_payload, SECRET_KEY, algorithm=ALGORITHM)
    
    return access_token, refresh_token