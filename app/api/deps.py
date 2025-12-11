from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core import security
from app.services.worker import worker_service
# หากคุณใช้ Pydantic Settings หรือ Schema ก็นำเข้าที่นี่ได้

# กำหนด URL สำหรับ Login (เพื่อให้ Swagger UI ใช้งานได้)
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login/website")

# def get_current_payload(token: str = Depends(oauth2_scheme)) -> dict:
#     """
#     Base Dependency: ตรวจสอบว่า Token ถูกต้องหรือไม่ (Signature ถูก, ไม่หมดอายุ)
#     """
#     payload = security.decode_access_token(token)
#     if payload is None:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Could not validate credentials",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     return payload

# def get_current_web_user(payload: dict = Depends(get_current_payload)) -> dict:
#     """
#     Dependency สำหรับ 'User บนหน้าเว็บ' เท่านั้น
#     - ใช้ใน Router: download_worker_zip
#     """
#     role = payload.get("role")
    
#     # อนุญาตเฉพาะ role 'user' หรือ 'admin' (แล้วแต่ Design)
#     if role not in ["user", "admin"]:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Access forbidden: Web users only"
#         )
        
#     return payload

# Endpoint ที่ใช้แลก Token (ใส่ให้ Swagger UI รู้จัก)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/workers/auth")

def get_current_agent(token: str = Depends(oauth2_scheme)):
    """
    ตรวจสอบ JWT Token สำหรับ Agent
    """
    # 1. แกะ Token
    payload = security.decode_access_token(token)
    
    if payload is None:
        print(f"❌ Debug: Token decode returned None")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 2. เช็ค Role
    role = payload.get("role")
    if role != "agent":
        print(f"❌ Debug: Role mismatch. Got {role}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not an agent identity"
        )
        
    # 3. เช็คว่ามี Worker ID นี้อยู่จริงไหม
    worker_id = payload.get("sub") 
    print(f"🔍 Debug: Checking Worker ID from token: {worker_id}")

    try:
        worker_id = int(worker_id) # แปลงเป็น int ให้ตรงกับใน JSON
    except (ValueError, TypeError):
         print("❌ Debug: Invalid Worker ID format")
         raise HTTPException(status_code=401, detail="Invalid Worker ID in token")

    # 4. ใช้ Service ค้นหาใน workers.json
    worker = worker_service.get_worker_by_id(worker_id)
    
    if not worker:
        print(f"❌ Debug: Worker ID {worker_id} not found in DB")
        raise HTTPException(status_code=404, detail="Worker not found")
        
    if worker.get("status") != "active":
        print(f"❌ Debug: Worker is {worker.get('status')}")
        raise HTTPException(status_code=403, detail="Worker is inactive")

    return worker