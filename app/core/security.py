import secrets

from datetime import datetime, timedelta
from typing import Optional, Union, Any
from jose import jwt, JWTError
from app.core.config import settings 
from passlib.context import CryptContext
import hashlib
import base64
# สมมติว่า config.py คุณมี settings.SECRET_KEY, settings.ALGORITHM

def create_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    สร้าง JWT Token
    :param data: Dictionary ข้อมูลที่จะฝังใน Token (เช่น sub, role, owner)
    :param expires_delta: ระยะเวลาหมดอายุ (ถ้าไม่ใส่จะใช้ค่า Default)
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # Default 30 นาที (หรือตาม Config)
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # เพิ่ม field 'exp' (Expiration Time) มาตรฐานของ JWT
    to_encode.update({"exp": expire})
    
    # Sign Token ด้วย Secret Key
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """
    แกะ JWT Token กลับเป็น Dictionary
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError as e:
        print(f"❌ JWT Decode Error: {e}")
        return None
    
def generate_access_key() -> str:
    """สร้าง Access Key แบบสุ่ม"""
    return secrets.token_urlsafe(32)

#PAssword hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def _prehash(password: str) -> str:
    """SHA-256 pre-hash to bypass bcrypt's 72-byte limit."""
    digest = hashlib.sha256(password.encode()).digest()
    return base64.b64encode(digest).decode()  # base64 keeps it bcrypt-safe

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(_prehash(plain_password), hashed_password)

def get_password_hash(password: str) -> str:
    prehashed = _prehash(password)
    print(f"DEBUG pre-hash length: {len(prehashed)}")
    return pwd_context.hash(_prehash(password))
