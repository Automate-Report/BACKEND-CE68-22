import json
import os
import io
import zipfile
import jwt

from datetime import datetime, timedelta
from typing import List
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
    __crptography_key = ""
    SECRET_KEY: str = "super-secret-key-fixed-value-1234567890"
    
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

    def _get_cipher(self):
        dynamic_key = Fernet.generate_key() 
        self.__crptography_key = dynamic_key
        cipher = Fernet(dynamic_key)
        return cipher
    
    def _get_crptography_key(self):
        return self.__crptography_key
    
    def _find_exe(self):
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        EXE_PATH = os.path.join(BASE_DIR, "static", "bin", "worker_agent.exe")
    
        if not os.path.exists(EXE_PATH):
            return {
                "code": 500,
                "content": "Server Error: Worker executable not found."
            }
        return {
            "code": 200,
            "content": EXE_PATH
        }
    
    def _create_token(self, worker_id:int, user: dict):
        token = security.create_token(
            data={
                "sub": str(worker_id), # ID ของ Worker ที่ user กด download
                "type": "registration", 
                "owner": user["sub"] # ผูกกับ User คนที่กดโหลด
            },
            expires_delta=timedelta(days=1)
        )
        return token
    
    def _encryption(self, data: dict, cipher):
        return cipher.encrypt(json.dumps(data).encode())


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

        if (not access_key.get("key")) or req.key != access_key.get("key"):
            raise HTTPException(status_code=403, detail=f"Invalid access key {access_key.get("key")}")
        
        target_worker["hostname"] = req.hostname
        self._save_json(workers)

        token = jwt.encode(
            {
                "sub": str(req.worker_id),
                "exp": datetime.utcnow() + timedelta(minutes=1)
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
            worker_access_key = access_key_service.get_access_key_by_id(access_key_id)

            
            if not worker_access_key.get("key"):
                raise HTTPException(status_code=401, detail="Worker not found")

            # ---------------------------------------------------
            # ขั้นตอนที่ 3: ตรวจสอบจริง (Verify)
            # รอบนี้ใช้ Key ของเจ้าตัวจริงๆ ถ้า Token ถูกปลอมแปลงมา จะ Error ตรงนี้
            # ---------------------------------------------------
            payload = jwt.decode(token, worker_access_key.get("key"), algorithms=["HS256"])
            
            return payload.get("sub")

        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
        except ValueError:
            # กันกรณี sub ไม่ใช่ตัวเลข
            raise HTTPException(status_code=401, detail="Invalid Worker ID format")
    
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


    
    # def process_task(self, worker_id: int, task_data: dict): # แก้ type hint ให้รับ dict หรือ model ตามที่คุณใช้
    #     """
    #     Service: รับรายงานผล (Heartbeat)
    #     แก้ไข: เพิ่มระบบ Auto-fix เพื่อแก้ปัญหา 403 ถาวร
    #     """
    #     workers = self._read_json()
    #     target_worker = None
        
    #     # 1. หา Worker (แปลงเป็น String เพื่อความชัวร์)
    #     print(f"🔍 Debug: Processing task for Worker ID: {worker_id}")
        
    #     for worker in workers:
    #         if str(worker["id"]) == str(worker_id):
    #             target_worker = worker
    #             break
        
    #     # 2. ถ้าหาไม่เจอจริงๆ ให้ 404
    #     if not target_worker:
    #         print(f"❌ Error: Worker ID {worker_id} not found in DB")
    #         raise HTTPException(status_code=404, detail="Worker ID not found")

    #     # 3. ✅ จุดแก้ไขปัญหา 403 (Auto-Fix Logic)
    #     # แทนที่จะดีด Error เราจะเช็คและ "ซ่อม" ค่าให้ถูกต้อง
    #     if target_worker.get("isActive") is False:
    #         print(f"⚠️ Warning: Worker {worker_id} status is Inactive.")
    #         print(f"🛠️ Auto-Fixing: Forcing isActive = True to bypass 403...")
            
    #         # --- บังคับเปิดใช้งานทันที ---
    #         target_worker["isActive"] = True 
    #         # --------------------------
            
    #         # หมายเหตุ: ใน Production จริง ควรใช้ raise HTTPException(403) 
    #         # แต่ในช่วง Dev ที่ข้อมูลเพี้ยน ให้ใช้แบบนี้เพื่อให้ผ่านไปได้ก่อน

    #     # 4. อัปเดตข้อมูล Heartbeat
    #     current_time = str(datetime.now())
    #     target_worker["updated_at"] = current_time
    #     target_worker["last_seen"] = current_time
    #     target_worker["status"] = "online" # ยืนยันสถานะ
        
    #     # (Optional) เก็บ Log Task
    #     # if hasattr(task_data, 'iteration'):
    #     #     target_worker["last_iteration"] = task_data.iteration 
    #     # 5. บันทึกข้อมูลลงไฟล์
    #     self._save_json(workers)
        
    #     print(f"✅ Success: Worker {worker_id} updated. Status: Online")

    #     return {
    #         "status": "success",
    #         "message": "Task processed successfully",
    #         "server_time": current_time
    #     }


worker_service = WorkerService()