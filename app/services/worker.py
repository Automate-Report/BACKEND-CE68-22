import json
import os
import io
import zipfile

from datetime import datetime, timedelta
from typing import List
from fastapi import Response, HTTPException
from fastapi.responses import StreamingResponse
from cryptography.fernet import Fernet

from app.schemas.worker import WorkerCreate, HandshakeRequest, TaskSubmitRequest
from app.core import security

# 1. หา Path ของไฟล์ JSON (เพื่อให้รันได้ไม่ว่าจะอยู่ folder ไหน)
# app/services/project.py -> ขึ้นไป 3 ชั้นคือ root folder (backend)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSON_FILE_PATH = os.path.join(BASE_DIR, "dummy_data", "workers.json")

class WorkerService:
    __crptography_key = ""
    
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
            "name": worker_in.name,
            "access_key_id": worker_in.access_key_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": "inactive"
        }
        
        # 3. บันทึก
        workers.append(new_worker)
        self._save_json(workers)

        return new_worker

    def get_worker_by_id(self, worker_id: int):
        """Service: ดึงข้อมูล 1 Worker"""
        workers = self._read_json()

        for worker in workers:
            if worker_id == worker["id"]:
                return worker
            
        return None
    
    def download_worker(self, worker_id: int, current_user: dict):
        """Service: download Worker"""
        isEXEpath = self._find_exe()

        if isEXEpath["code"] == 500:
            return Response(content=isEXEpath["content"], status_code=isEXEpath["code"])
        
        exe_path = isEXEpath["content"]

        reg_token = self._create_token(worker_id=worker_id, user=current_user)

        secret_data = {
            "worker_id": worker_id,
            "registration_token": reg_token,
            "owner": current_user["sub"],
            "created_at": str(datetime.now()),
            "api_key": None
        }    
    
        # ไฟล์ Config ทั่วไป
        config_data = {
            "api_url": "http://127.0.0.1:8000", # หรือ URL ของ Production
            "task_interval_seconds": 60,
            "log_level": "INFO"
        }

        cipher = self._get_cipher()
        encrypted_secret = self._encryption(data=secret_data, cipher=cipher)
        encrypted_config = self._encryption(data=config_data, cipher=cipher)
 

        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # 1. ใส่ไฟล์ .exe
            zip_file.write(exe_path, arcname="worker_agent.exe")
            
            # 2. ใส่ไฟล์ .worker_secret (แปลง dict -> json string)
            zip_file.writestr("secret.dat", encrypted_secret)
            
            # 3. ใส่ไฟล์ worker_config.json
            zip_file.writestr("config.dat", encrypted_config)

            # 4. ใส่ไฟล์ .system_lock
            zip_file.writestr(".system_lock", self._get_crptography_key())

        # เลื่อน Pointer กลับไปหัวแถว เตรียมส่งออก
        zip_buffer.seek(0)

        # --- E. ส่งกลับให้ Browser ดาวน์โหลด ---
        headers = {
            "Content-Disposition": f'attachment; filename="worker_agent_{worker_id}.zip"'
        }
        
        return StreamingResponse(
            zip_buffer, 
            media_type="application/zip", 
            headers=headers
        )
    
    def worker_handshake(self, req: HandshakeRequest):
        # A. ตรวจสอบ Registration Token
        payload = security.decode_access_token(req.registration_token)

        if not payload or payload.get("type") != "registration":
            raise HTTPException(status_code=400, detail="Invalid registration token")
        
        token_worker_id = payload.get("sub") # "sub" เป็น worker_id

        workers = self._read_json()
        hasWorker = None
        for worker in workers:
            if token_worker_id == str(worker["id"]):
                if worker["status"] == "active":
                    # อาจจะยอมให้ Re-key หรือจะ Error ก็ได้แล้วแต่ Policy
                    pass

                new_api_key = security.generate_api_key()
                worker["status"] = "active"
                worker["api_key"] = new_api_key
                worker["hostname"] = req.hostname
                worker["activated_at"] = str(datetime.now())
                self._save_json(workers)
                return {
                    "status": "success",
                    "agent_id": str(hasWorker),
                    "api_key": new_api_key
                }

        raise HTTPException(status_code=404, detail="Worker ID not found")
    
    def auth(self, req: HandshakeRequest):
        workers = self._read_json()

        for worker in workers:
            if worker["api_key"] == req.api_key:
                if worker["status"] != "active":
                    return HTTPException(status_code=403, detail="Worker is inactive or revoked")
            
            # สร้าง Session Token (JWT) อายุ 15 นาที
            session_token = security.create_token(
                data={
                    "sub": str(worker["id"]), 
                    "role": "agent",
                    "owner": str(worker["id"])
                },
                expires_delta=timedelta(minutes=15)
            )
        
        return {
            "access_token": session_token,
            "token_type": "bearer",
            "expires_in": 900
        }
    
    def process_task(self, worker_id: int, task_data: TaskSubmitRequest):
        """
        บันทึกการทำงาน: อัปเดตเวลา updated_at ของ Worker
        """
        workers = self._read_json()
        target_worker = None
        
        # 1. หา Worker และอัปเดตเวลา
        for worker in workers:
            if worker["id"] == worker_id:
                worker["updated_at"] = datetime.now().isoformat()
                # worker["last_iteration"] = task_data.iteration # (Optional) เก็บ Log รอบล่าสุด
                target_worker = worker
                break
        
        if target_worker:
            self._save_json(workers)
            
            # --- (Optional) ถ้าอยากเก็บ Log งานแยกอีกไฟล์ ---
            # self._append_to_task_log(worker_id, task_data)
            
            print(f"✅ [Worker {worker_id}] Reported task: Iteration {task_data.iteration}")
            return {
                "status": "success",
                "message": f"Task iteration {task_data.iteration} received"
            }
            
        return {"status": "error", "message": "Worker not found"}


worker_service = WorkerService()