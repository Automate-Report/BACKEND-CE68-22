import secrets

from datetime import datetime, timedelta
from typing import Optional, Union, Any
from jose import jwt, JWTError
from app.core.config import settings 
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
    
def generate_api_key() -> str:
    """สร้าง API Key แบบสุ่มยาว 64 ตัวอักษร"""
    return secrets.token_hex(32)
    
