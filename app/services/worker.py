import json
import os
import io
import zipfile
import jwt

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import Response, HTTPException, Header
from fastapi.responses import StreamingResponse
from cryptography.fernet import Fernet

from app.schemas.worker import WorkerCreate, HandshakeRequest, VerifyRequest
from app.core import security
from app.services.access_key import access_key_service

# 1. หา Path ของไฟล์ JSON (เพื่อให้รันได้ไม่ว่าจะอยู่ folder ไหน)
# app/services/project.py -> ขึ้นไป 3 ชั้นคือ root folder (backend)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSON_FILE_PATH = os.path.join(BASE_DIR, "dummy_data", "workers.json")

class WorkerService:
    
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

    def _enrich_worker_status(self, worker):
        """ฟังก์ชันช่วยคำนวณสถานะของ Worker"""
        OFFLINE_THRESHOLD_SECONDS = 600
        
        # 1. เช็คเรื่อง Key ก่อน (สำคัญสุด)
        if not worker.get("access_key_id"):
            worker["status"] = "Revoked" # โดนถอดสิทธิ์
            return worker

        # 2. เช็คเรื่องเวลา (Online/Offline)
        last_seen_str = worker.get("last_heartbeat")
        
        if not last_seen_str:
            worker["status"] = "offline" # ไม่เคยต่อเน็ตเลย
            return worker

        # แปลง String กลับเป็น datetime
        try:
            last_seen = datetime.fromisoformat(last_seen_str)
            time_diff = datetime.utcnow() - last_seen

            if time_diff.total_seconds() < OFFLINE_THRESHOLD_SECONDS:
                worker["status"] = "online"
            else:
                worker["status"] = "offline"
                
        except ValueError:
            worker["status"] = "Unknown"

        return worker

    def create_worker(self, worker_in: WorkerCreate, user_id: int) -> dict:
        """Service: สร้าง Worker"""
        workers = self._read_json()
        
        # 1. จำลอง Logic Auto Increment ID
        new_id = 1
        if workers:
            # เอา ID ตัวสุดท้ายมา + 1
            new_id = workers[-1]["id"] + 1
            
        # 2. แปลงจาก Pydantic Schema เป็น Dict และเติมข้อมูล System (ID, Time)
        new_worker = {
            "id": new_id,
            "user_id": user_id,
            "name": worker_in.name,
            "hostname": None,
            "access_key_id": None,
            "status": "offline",
            "isActive": False,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # 3. บันทึก
        workers.append(new_worker)
        self._save_json(workers)

        return new_worker
    
    def get_all_workers(self, user_id: int, page: int, size: int, sort_by: str = None, order: str = "asc"):
        """Service: ดึงข้อมูล Worker ทั้งหมดของ user นั้น"""
        workers = self._read_json()
        
        # 1. กรอง User
        all_matches = []
        for worker in workers:
            worker = self._enrich_worker_status(worker)
            if worker["user_id"] == user_id:
                all_matches.append(worker)


        if sort_by:
            reverse = (order == "desc")
            # Handle กรณี field ไม่มีอยู่จริง หรือต้องการ sort date
            all_matches.sort(key=lambda x: x.get(sort_by, ""), reverse=reverse)
        
        # 2. นับจำนวนทั้งหมด (สำหรับ Pagination UI)
        total_count = len(all_matches)
            
        # 3. คำนวณ Pagination Logic
        import math
        total_pages = math.ceil(total_count / size)
        
        offset = (page - 1) * size
        
        # --- จุดที่ต้องแก้: ตัดข้อมูล (Slicing) ---
        # ใช้ Python Slice [start : end]
        paginated_items = all_matches[offset : offset + size]

        self._save_json(workers)
        return {
            "total": total_count,      # จำนวนทั้งหมด (เช่น 50)
            "page": page,
            "size": size,
            "total_pages": total_pages,
            "items": paginated_items   # ส่งกลับเฉพาะ 10 ตัวของหน้านั้น (ไม่ใช่ทั้งหมด)
        }
    
    def delete_worker(self, worker_id: int, user_id: int) -> bool:
        """Service: ลบ Worker"""
        workers = self._read_json()
        for i, worker in enumerate(workers):
            if worker["id"] == worker_id and worker["user_id"] == user_id:
                del workers[i]
                self._save_json(workers)
                return True
        return False
    

    def get_worker_by_id(self, user_id:int, worker_id: int):
        """Service: ดึงข้อมูล 1 Worker"""
        workers = self._read_json()

        for worker in workers:
            if worker_id == worker["id"]:
                return worker
            
        return None
    
    def update_worker(self, worker_id: int, worker_in: WorkerCreate, user_id: int) -> Optional[dict]:
        """Service: อัปเดต Worker"""
        workers = self._read_json()
        for worker in workers:
            if worker["id"] == worker_id and worker["user_id"] == user_id:
                worker["name"] = worker_in.name
                worker["updated_at"] = datetime.now().isoformat()
                self._save_json(workers)
                return worker
        return None
    
    def add_access_key(self, worker_id:int, access_key_id: int):
        """Service: add access key id ให้ worker id"""
        workers = self._read_json()

        for worker in workers:
            if worker_id == worker["id"]:
                worker["access_key_id"] = access_key_id

        self._save_json(workers)
        return None
    
    def remove_access_key(self, worker_id:int):
        """Service: remove access key id ให้ worker id"""
        workers = self._read_json()

        for worker in workers:
            if worker_id == worker["id"]:
                worker["access_key_id"] = None
                worker["isActive"] = False
                worker["status"] = "Revoked"
                worker["last_heartbeat"] = None

        self._save_json(workers)
        return None

    def verify_worker(self, req: VerifyRequest):
        workers = self._read_json()
        target_worker = None
        for worker in workers:
            if worker["id"] == req.worker_id:
                target_worker = worker

        if not target_worker:
            # Use 404 for "Not Found"
            raise HTTPException(status_code=404, detail="Worker ID not found")
        
        access_key_id = target_worker.get("access_key_id")

        
        if not access_key_id:
            raise HTTPException(status_code=400, detail="Worker missing access key")
        
        access_key = access_key_service.get_access_key_by_id(access_key_id)
        access_key_data = access_key.get("key")

        if (not access_key_data) or (not access_key):
            raise HTTPException(status_code=500, detail="Internal Error: Key data missing")
        
        current_access_key = access_key_data

        if req.key != current_access_key:
            # 🔥 CASE B: User กด "Generate New Key" ไปแล้ว
            # Agent (ที่ถือ Key เก่า) ส่งมาจะไม่ตรงกับ current_secret
            raise HTTPException(status_code=403, detail="Invalid Access Key (Key mismatch)")
        
        target_worker["hostname"] = req.hostname
        target_worker["isActive"] = True
        target_worker["status"] = "online"

        self._save_json(workers)

        token = jwt.encode(
            {
                "sub": str(req.worker_id),
                "exp": datetime.utcnow() + timedelta(minutes=30)
            },
            access_key.get("key"),
            algorithm="HS256"
        )

        return {
                "status": "success",
                "token": token
            }
    
    def verify_token(self, authorization: str = Header(None)):
        # ... extraction logic ...
        token = authorization.split(" ")[1]

        try:
            # ---------------------------------------------------
            # ขั้นตอนที่ 1 (The Strange Part): แอบดูไส้ในก่อน 
            # โดยยัง "ไม่ตรวจลายเซ็น" (verify_signature=False)
            # เพื่อเอาแค่ Worker ID ออกมาหา key
            # ---------------------------------------------------
            unverified_payload = jwt.decode(token, options={"verify_signature": False})
            worker_id = int(unverified_payload.get("sub"))

            # ---------------------------------------------------
            # ขั้นตอนที่ 2: ไปดึง Access Key ของ Worker คนนั้นมาจาก DB
            # ---------------------------------------------------
            # สมมติว่ามี function ดึง key จาก worker_id
            # (คุณอาจต้องเรียก service หรือ query db ตรงนี้)
            fake_user_id = 1
            worker = self.get_worker_by_id(user_id=fake_user_id, worker_id=worker_id) 
            if not worker:
                raise HTTPException(status_code=401, detail="Worker not found (ID invalid)")
            
            access_key_id = worker["access_key_id"]

            if not access_key_id:
                # ถ้าไม่มี ID แสดงว่าโดนถอดสิทธิ์แล้ว
                raise HTTPException(status_code=401, detail="Access Key Revoked")
            
            worker_access_key = access_key_service.get_access_key_by_id(access_key_id)
            real_secret = worker_access_key.get("key")
    
            if not real_secret:
                raise HTTPException(status_code=401, detail="Secret missing")

            # ---------------------------------------------------
            # ขั้นตอนที่ 3: ตรวจสอบจริง (Verify)
            # รอบนี้ใช้ Key ของเจ้าตัวจริงๆ ถ้า Token ถูกปลอมแปลงมา จะ Error ตรงนี้
            # ---------------------------------------------------
            payload = jwt.decode(token, real_secret, algorithms=["HS256"])
            
            return payload.get("sub")

        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid Token (Key mismatched or tampered)")
        except ValueError:
            # กันกรณี sub ไม่ใช่ตัวเลข
            raise HTTPException(status_code=401, detail="Invalid Worker ID format")
    
    def update_heartbeat(self, worker_id: int):
        workers = self._read_json()
        found = False

        for worker in workers:
            if worker["id"] == int(worker_id):
                worker["last_heartbeat"] = datetime.utcnow().isoformat()
                worker["status"] = "online"
                worker["isActive"] = True
                found = True

        if found:
            self._save_json(workers)
            return True
        return False
    
    def download_worker(self, worker_id: int):
        """Service: download Worker"""
        hidden_payload = {
            "WORKER_ID": worker_id,
            "BACKEND_URL": "http://127.0.0.1:8000"
        }

        fake_user_id = 1
        worker = self.get_worker_by_id(user_id=fake_user_id, worker_id=worker_id)

        EMBEDED_KEY = b'i-0yYzq1qgi--twBbVJBH6neq1xw38E8ZcJ7KdBVBjM='
        DELIMITER = b"|||HIDDEN_DATA|||"

        json_bytes = json.dumps(hidden_payload).encode()
        f = Fernet(EMBEDED_KEY)
        encrypted_payload = f.encrypt(json_bytes)

        with open("app/static/bin/worker_template.exe", "rb") as f:
            exe_data = f.read()

        final_exe = exe_data + DELIMITER + encrypted_payload

        return StreamingResponse(
            io.BytesIO(final_exe),
            media_type="application/vnd.microsoft.portable-executable",
            headers={"Content-Disposition": f"attachment; filename=worker_{worker.get("name")}.exe"}
        )




worker_service = WorkerService()