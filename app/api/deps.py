from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core import security
# หากคุณใช้ Pydantic Settings หรือ Schema ก็นำเข้าที่นี่ได้

# กำหนด URL สำหรับ Login (เพื่อให้ Swagger UI ใช้งานได้)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login/website")

def get_current_payload(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Base Dependency: ตรวจสอบว่า Token ถูกต้องหรือไม่ (Signature ถูก, ไม่หมดอายุ)
    """
    payload = security.decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload

def get_current_web_user(payload: dict = Depends(get_current_payload)) -> dict:
    """
    Dependency สำหรับ 'User บนหน้าเว็บ' เท่านั้น
    - ใช้ใน Router: download_worker_zip
    """
    role = payload.get("role")
    
    # อนุญาตเฉพาะ role 'user' หรือ 'admin' (แล้วแต่ Design)
    if role not in ["user", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Web users only"
        )
        
    return payload

def get_current_agent(payload: dict = Depends(get_current_payload)) -> dict:
    """
    Dependency สำหรับ 'Agent/Worker' เท่านั้น
    - ใช้ใน Router ที่ Agent ต้องยิงส่งงาน
    """
    role = payload.get("role")
    
    if role != "agent":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Agents only"
        )
    return payload