import json
import os
from datetime import datetime, timedelta, timezone
from typing import List
from jose import jwt, JWTError
from app.schemas.userauthen import LoginRequest, UserCreate
from app.core.config import settings
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from app.core.redis import redis_client

# 1. หา Path ของไฟล์ JSON (เพื่อให้รันได้ไม่ว่าจะอยู่ folder ไหน)
# app/services/project.py -> ขึ้นไป 3 ชั้นคือ root folder (backend)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSON_FILE_PATH = os.path.join(BASE_DIR, "dummy_data", "user.json")

class UserAuthenService:
    
    def _ensure_dummy_folder_exists(self):
        """ตรวจสอบว่ามี folder dummy_data หรือยัง ถ้าไม่มีให้สร้าง"""
        folder = os.path.dirname(JSON_FILE_PATH)
        if not os.path.exists(folder):
            os.makedirs(folder)

    def _read_json(self) -> List[dict]:
        """อ่านข้อมูลจากไฟล์ JSON"""
        if not os.path.exists(JSON_FILE_PATH):
            return []
        try:
            with open(JSON_FILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return [] # ถ้าไฟล์เสียหรือว่างเปล่า ให้คืนค่า list ว่าง
        
    def _save_json(self, data: List[dict]):
        """บันทึกข้อมูลลงไฟล์ JSON"""
        self._ensure_dummy_folder_exists()
        with open(JSON_FILE_PATH, "w", encoding="utf-8") as f:
            # default=str ช่วยแปลง datetime เป็น string อัตโนมัติ
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    def blacklist_token(self, token: str):
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        except JWTError as errormsg:
            print(errormsg)
            return  # Invalid token, cannot blacklist

        exp = payload["exp"]
        now = int(datetime.now(timezone.utc).timestamp())
        ttl = exp - now

        if ttl <= 0:
            return  # token already expired
        
        print("token blacklisted :", token)

        redis_client.setex(token, ttl, "blacklisted")

    def authenticate_user(self, loginRequest: LoginRequest):
        """Service: ตรวจสอบการเข้าสู่ระบบของผู้ใช้"""
        users = self._read_json()
        for user in users:
            # email และ password ตรงกัน
            if user["email"] == loginRequest.email and user["password"] == loginRequest.password:
                
                # create JWT
                now = datetime.now(timezone.utc)
                expire = now + timedelta(hours=1)
                payload = {
                    "sub": loginRequest.email,
                    "iat": int(now.timestamp()),
                    "exp": int(expire.timestamp())
                }
                print(now, expire)
                
                token = jwt.encode(
                    payload,
                    settings.SECRET_KEY,
                    algorithm=settings.ALGORITHM
                )

                return {
                "token": token,
                "user": {
                    "email": loginRequest.email,
                    "firstname": user["firstname"],
                    "lastname": user["lastname"]
                }
            }
            
        # Check all but user not found
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    def create_user(self, createUser: UserCreate):
        """Service: สร้างผู้ใช้ใหม่"""
        users = self._read_json()
        
        if any(u["email"] == createUser.email for u in users):
            raise HTTPException(status_code=400, detail="Email already registered")

        else:
            new_user = {
                "firstname": createUser.firstName,
                "lastname": createUser.lastName,
                "email": createUser.email,
                "password": createUser.password,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "session_token": None,
                "google_id": None,
                "picture": None
            }
            
            users.append(new_user)
            self._save_json(users)
            
            # Only return non-sensitive info
            return {
                "email": createUser.email,
                "firstname": createUser.firstName,
                "lastname": createUser.lastName
            }

        
# สร้าง instance ของ Service เพื่อใช้งาน
userauthen_service = UserAuthenService()