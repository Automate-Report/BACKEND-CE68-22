import json
import os
import io
import zipfile
import jwt

from cvss import CVSS3
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import HTTPException, Header
from fastapi.responses import StreamingResponse
from cryptography.fernet import Fernet

from app.core import security
from app.schemas.worker import WorkerCreate, VerifyRequest, HeartBeatPayload
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

        # 1. เช็คเรื่องเวลา (Online/Offline)
        last_seen_str = worker.get("last_heartbeat")
        
        if not last_seen_str:
            worker["status"] = "notActivated" # ไม่เคยต่อเน็ตเลย
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

    def create_worker(self, worker_in: WorkerCreate, project_id: int) -> dict:
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
            "project_id": project_id,
            "thread_number": worker_in.thread_number,
            "current_load": 0,
            "name": worker_in.name,
            "hostname": None,
            "status": "offline",
            "isActive": False,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "last_heartbeat": None,
            "owner": None,
        }
        
        # 3. บันทึก
        workers.append(new_worker)
        self._save_json(workers)

        return new_worker
    
    def get_all_workers_by_project_id(self, project_id: int, page: int, size: int, sort_by: str = None, order: str = "asc"):
        """Service: ดึงข้อมูล Worker ทั้งหมดของ user นั้น"""
        workers = self._read_json()
        
        # 1. กรอง User
        all_matches = []
        for worker in workers:
            worker = self._enrich_worker_status(worker)
            if worker["project_id"] == project_id:
                all_matches.append(worker)

        if sort_by:
            reverse = (order == "desc")
            # Handle กรณี field ไม่มีอยู่จริง หรือต้องการ sort date
            all_matches.sort(key=lambda x: (x.get(sort_by) or ""), reverse=reverse)
        
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
    
    def delete_worker(self, worker_id: int, user_id: str) -> bool:
        """Service: ลบ Worker"""
        workers = self._read_json()
        for i, worker in enumerate(workers):
            if worker["id"] == worker_id and worker["email"] == user_id:
                del workers[i]
                self._save_json(workers)
                return True
        return False
    

    def get_worker_by_id(self, worker_id: int):
        """Service: ดึงข้อมูล 1 Worker"""
        workers = self._read_json()

        for worker in workers:
            if worker_id == worker["id"]:
               return worker
            
        return None
    
    def update_worker(self, worker_id: int, worker_in: WorkerCreate, user_id: str) -> Optional[dict]:
        """Service: อัปเดต Worker"""
        workers = self._read_json()
        for worker in workers:
            if worker["id"] == worker_id and worker["email"] == user_id:
                worker["name"] = worker_in.name
                worker["updated_at"] = datetime.now().isoformat()
                self._save_json(workers)
                return worker
        return None
    
    def get_summary_info(self, project_id: int):
        """Get Total Workers, Online Status, Busy(current_load != 0), total jobs"""
        workers = self._read_json()
        total_worker = 0
        online = 0
        busy = 0
        total_job = 0

        for worker in workers:
            if worker["project_id"] == project_id:
                total_worker+=1
                if worker["status"] == "online":
                    online+=1
                if worker["current_load"] > 0:
                    busy+=1

        return {
            "total": total_worker,
            "online": online,
            "busy": busy,
            "total_jobs": total_job
        }
    
    def get_all_worker_ids_by_project_id(self, project_id: int):
        workers = self._read_json()

        result = []
        for worker in workers:
            if worker["project_id"] == project_id:
                result.append(worker["id"])
        
        return result
    
    def change_access_key(self, access_key_id: int, worker_id: int):
        workers = self._read_json()
        isChange = False
        for worker in workers:
            if worker["id"] == worker_id:
                worker["access_key_id"] = access_key_id
                worker["status"] = "notActivated"
                worker["isActive"] = False
                worker["last_heartbeat"] = None
                worker["internal_ip"] = None
                worker["hostname"] = None
                isChange = True
        self._save_json(workers)

        if isChange: 
            return True
        return False
    
    def disconnect_worker(self, worker_id: int):
        workers = self._read_json()
        for worker in workers:
            if worker["id"] == worker_id:
                worker["isActive"] = False
                worker["hostname"] = None
                worker["internal_ip"] = None
                worker["last_heartbeat"] = None

        self._save_json(workers)

    def disconnect_workers_in_project(self, project_id: int):
        workers = self._read_json()
        for worker in workers:
            if worker["project_id"] == project_id:
                worker["isActive"] = False
                worker["hostname"] = None
                worker["internal_ip"] = None
                worker["last_heartbeat"] = None

        self._save_json(workers)

    def verify_worker(self, req: VerifyRequest):
        workers = self._read_json()
        target_worker = None
        for worker in workers:
            if worker["id"] == req.worker_id:
                target_worker = worker

        if not target_worker:
            # Use 404 for "Not Found"
            raise HTTPException(status_code=404, detail="Worker ID not found")
        
        access_key_id = target_worker["access_key_id"]
        access_key = access_key_service.get_access_key_by_id(access_key_id)

        
        if not access_key:
            raise HTTPException(status_code=400, detail="Worker missing access key")
        
        current_access_key = access_key.get("key")
        print(current_access_key)

        if req.key != current_access_key:
            raise HTTPException(status_code=403, detail="Invalid Access Key (Key mismatch)")
        
        target_worker["hostname"] = req.hostname
        target_worker["isActive"] = True
        target_worker["status"] = "online"
        target_worker["internal_ip"] = req.internal_ip

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
            worker = self.get_worker_by_id(worker_id=worker_id) 
            if not worker:
                raise HTTPException(status_code=401, detail="Worker not found (ID invalid)")
            
            access_key_id = worker["access_key_id"]
            
            access_key = access_key_service.get_access_key_by_id(access_key_id)

            if not access_key:
                # ถ้าไม่มี ID แสดงว่าโดนถอดสิทธิ์แล้ว
                raise HTTPException(status_code=401, detail="Access Key Revoked")
            
            real_secret = access_key.get("key")
    
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
    
    def update_heartbeat(self, worker_id: int, payload: HeartBeatPayload):
        workers = self._read_json()
        found = False

        for worker in workers:
            if worker["id"] == int(worker_id):
                worker["current_load"] = payload.current_load
                worker["last_heartbeat"] = datetime.utcnow().isoformat()
                worker["status"] = payload.status
                worker["isActive"] = True
                worker["internal_ip"] = payload.internal_ip
                worker["hostname"] = payload.hostname
                found = True
                break

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
        worker = self.get_worker_by_id(worker_id=worker_id)

        EMBEDED_KEY = b'JimGiFbXqlAwUAXu2PM1_eATccCMR7uAoB0wfI2DMgQ='
        DELIMITER = b"|||HIDDEN_DATA|||"


        json_bytes = json.dumps(hidden_payload).encode() # worker_id + backend_url
        f = Fernet(EMBEDED_KEY) # สร้างตัวเข้ารหัส
        encrypted_payload = f.encrypt(json_bytes) # เข้ารหัส

        # Path ของ Worker
        TEMPLATE_DIR = "app/static/bin/SecurityWorker" 
        # ชื่อไฟล์ exe 
        TARGET_EXE_NAME = "SecurityWorker.exe"

        # --- ส่วนที่แก้ไข: สร้าง ZIP File ในหน่วยความจำ ---
        zip_buffer = io.BytesIO()

        dest_folder_name = f"SecurityWorker_{worker.get('name')}"

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        
            # วนลูปอ่านทุกไฟล์ใน Folder Template
            for root, dirs, files in os.walk(TEMPLATE_DIR):
                for filename in files:
                    # Path เต็มของไฟล์ในเครื่อง Server
                    abs_path = os.path.join(root, filename)
                    
                    # Path สัมพัทธ์ (Relative) เพื่อใช้จัดโครงสร้างใน Zip
                    # เช่น ถ้าไฟล์อยู่ template/internal/lib.dll -> rel_path จะเป็น internal/lib.dll
                    rel_path = os.path.relpath(abs_path, TEMPLATE_DIR)
                    
                    # Path ปลายทางใน Zip (เอาชื่อโฟลเดอร์ worker มานำหน้า)
                    zip_arcname = os.path.join(dest_folder_name, rel_path)

                    # --- จุดสำคัญ: เช็คว่าเป็นไฟล์ exe หลักหรือไม่ ---
                    if filename == TARGET_EXE_NAME:
                        # ถ้าใช่: อ่านมา + ฝัง payload + เขียนลง zip (writestr)
                        with open(abs_path, "rb") as f_exe:
                            exe_data = f_exe.read()
                        
                        final_exe_data = exe_data + DELIMITER + encrypted_payload #ฉีดข้อมูล worker_id + backend_url
                        zf.writestr(zip_arcname, final_exe_data)
                    
                    else:
                        # ถ้าไม่ใช่ (เป็นพวก dll, _internal): จับยัดลง zip เลย (write)
                        zf.write(abs_path, arcname=zip_arcname)

        # 4. ส่งไฟล์กลับ
        zip_buffer.seek(0)
            
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={dest_folder_name}.zip"
            }
        )

    def read_all_worker(self, project_id: int):
        workers = self._read_json()
        result = []
        for w in workers:
            if w["project_id"] == project_id:
                result.append(w)

        return result


worker_service = WorkerService()