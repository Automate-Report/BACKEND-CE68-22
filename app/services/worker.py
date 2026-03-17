import json
import os
import io
import zipfile
import jwt
import math

from datetime import datetime, timedelta, timezone
from typing import List, Optional
from fastapi import HTTPException, Header
from fastapi.responses import StreamingResponse
from cryptography.fernet import Fernet

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.workers import Worker, WorkerStatus
from app.models.users import User
from app.models.jobs import Job, JobStatus

from app.core.config import settings
from app.schemas.worker import WorkerCreate, VerifyRequest, HeartBeatPayload
from app.services.access_key import access_key_service


class WorkerService:
    
    def _enrich_worker_status(self, worker_data: dict):
        """ฟังก์ชันช่วยคำนวณสถานะของ Worker"""
        OFFLINE_THRESHOLD_SECONDS = 600

        # 1. เช็คเรื่องเวลา (Online/Offline)
        last_seen_str = worker_data.get("last_heartbeat")
        
        if not last_seen_str or not worker_data.get("owner"):
            worker_data["status"] = WorkerStatus.NOT_ACTIVATE
            return worker_data
        
        now = sa.sql.func.now()
        # แปลง String กลับเป็น datetime
        try:
            last_seen = datetime.fromisoformat(last_seen_str)
            time_diff = datetime.utcnow() - last_seen

            if time_diff.total_seconds() < OFFLINE_THRESHOLD_SECONDS:
                worker_data["status"] = WorkerStatus.ONLINE
            else:
                worker_data["status"] = WorkerStatus.OFFLINE
                
        except ValueError:
            worker_data["status"] = WorkerStatus.UNKNOWN

        return worker_data

    async def create_worker(self, worker_in: WorkerCreate, project_id: int, access_key_id: int, db: AsyncSession) -> dict:
        """Service: สร้าง Worker"""
        new_worker_db = Worker(
            project_id = project_id,
            access_key_id = access_key_id,
            thread_number = worker_in.thread_number,
            current_load = 0,
            name = worker_in.name,
            hostname = None,
            is_active = False,
            last_heartbeat = None,
            owner = None,
        )
        
        try:
            db.add(new_worker_db)
            await db.commit()

            await db.refresh(new_worker_db)
        except Exception as e:
            await db.rollback()
            print(f"DEBUG ERROR: {e}")
            raise HTTPException(status_code=500, detail="Could not create worker")
            
        # 2. แปลงจาก Pydantic Schema เป็น Dict และเติมข้อมูล System (ID, Time)
        new_worker = {
            "id": new_worker_db.id,
            "project_id": new_worker_db.project_id,
            "access_key_id": new_worker_db.access_key_id,
            "thread_number": new_worker_db.thread_number,
            "current_load": new_worker_db.current_load,
            "name": new_worker_db.name,
            "hostname": new_worker_db.hostname,
            "status": new_worker_db.status,
            "is_active": new_worker_db.is_active,
            "created_at": new_worker_db.created_at,
            "updated_at": new_worker_db.updated_at,
            "last_heartbeat": new_worker_db.last_heartbeat,
            "owner": new_worker_db.owner,
        }

        return new_worker
    
    async def get_all_workers_by_project_id(self, project_id: int, page: int, size: int, db: AsyncSession, sort_by: str = None, order: str = "asc", search: str = None, filter: str = "ALL"):
        """Service: ดึงข้อมูล Worker ทั้งหมดของ user นั้น"""
        query = (
            sa.select(Worker, User.first_name, User.last_name)
            .join(User, Worker.owner == User.email, isouter=True)
            .where(Worker.project_id == project_id)
        )

        if search:
            query = query.where(Worker.name.ilike(f"%{search}%"))

        if filter and filter != "ALL":
            if filter == "online":
                query = query.where(Worker.status == WorkerStatus.ONLINE)
            elif filter == "offline":
                query = query.where(Worker.status == WorkerStatus.OFFLINE)
            elif filter == "notActivated":
                query = query.where(Worker.status == WorkerStatus.NOT_ACTIVATE)
            elif filter == "available":
                query = query.where(Worker.owner == None)
            elif filter == "inUse":
                query = query.where(Worker.owner != None)

        if sort_by:
            column = getattr(Worker, sort_by, Worker.created_at)
            if order == "desc":
                query = query.order_by(column.desc())
            else:
                query = query.order_by(column.asc())

        count_query = sa.select(sa.sql.func.count()).select_from(query.subquery())
        total_count_result = await db.execute(count_query)
        total_count = total_count_result.scalar() or 0

        # 4. Sorting
        column = getattr(Worker, sort_by if sort_by else "created_at", Worker.created_at)
        query = query.order_by(column.desc() if order == "desc" else column.asc())

        # 5. SQL-Level Pagination (LIMIT & OFFSET)
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        # 6. Execute Final Query
        result = await db.execute(query)
        rows = result.all() # Returns list of tuples: (Worker, first_name, last_name)

        # 7. Format the output
        paginated_items = []
        for worker, fn, ln in rows:
            worker_dict = worker.__dict__.copy() # Convert to dict
            worker_dict.pop('_sa_instance_state', None) # Clean up internal SA state
            worker_dict["owner_name"] = f"{fn} {ln}"
            worker_dict = self._enrich_worker_status(worker_dict)
            paginated_items.append(worker_dict)

        return {
            "total": total_count,
            "page": page,
            "size": size,
            "total_pages": math.ceil(total_count / size),
            "items": paginated_items
        }
    
    async def delete_worker(self, worker_id: int, db: AsyncSession) -> bool:
        """Service: ลบ Worker"""
        query = sa.select(Worker).where(Worker.id == worker_id)
        result = await db.execute(query)
        worker = result.scalar_one_or_none()

        if not worker:
            return None
        
        try:
            # 2. Delete using the session
            await db.delete(worker)
            
            # 3. Commit the transaction
            await db.commit()
            return True
        except Exception as e:
            # 4. Rollback if something goes wrong (e.g., Foreign Key constraint)
            await db.rollback()
            print(f"Delete Error: {e}")
            return False
    
    async def get_worker_by_id(self, worker_id: int, db: AsyncSession):
        """Service: ดึงข้อมูล 1 Worker"""
        query = sa.select(Worker, User.first_name, User.last_name).join(User, Worker.owner == User.email, isouter=True).where(Worker.id == worker_id)
        result = await db.execute(query)
        row = result.first()

        if not row:
            return None

        worker_dict = row[0].__dict__.copy()
        worker_dict.pop('_sa_instance_state', None) # Clean up internal SA state
        worker_dict["owner_name"] = f"{row[1]} {row[2]}"
        worker_dict = self._enrich_worker_status(worker_dict)
        
        return worker_dict
    
    async def update_worker(self, worker_id: int, worker_in: WorkerCreate, user_id: str, role: str, db: AsyncSession):
        """Service: อัปเดต Worker"""
        query = sa.select(Worker, User.first_name, User.last_name).join(User, Worker.owner == User.email, isouter=True).where(Worker.id == worker_id)
        result = await db.execute(query)
        row = result.first()

        if not row:
            return None
        
        worker_db = row[0]
        first_name = row[1]
        last_name = row[2]
        
        if worker_db.owner != user_id and role == "pentester":
            raise HTTPException(status_code=403, detail="Worker does not belong to the user")
        
        worker_db.name = worker_in.name
        worker_db.thread_number = worker_in.thread_number

        try:
            await db.commit()
            await db.refresh(worker_db) # This ensures all DB-generated fields are loaded

            worker_dict = row[0].__dict__.copy()
            worker_dict.pop('_sa_instance_state', None) # Clean up internal SA state
            worker_dict["owner_name"] = f"{first_name} {last_name}"
            return worker_dict
        except Exception as e:
            await db.rollback()
            # Log the error so you can see it in the terminal
            print(f"Database Error: {e}") 
            raise HTTPException(status_code=500, detail="Internal Server Error")
    
    async def get_summary_info(self, project_id: int, db: AsyncSession):
        """Get Total Workers, Online Status, Busy(current_load != 0), total jobs"""
        # Define the same threshold as your enrichment function (600s = 10 minutes)
        OFFLINE_THRESHOLD = timedelta(seconds=600)

        # Logic for dynamic status:
        # 1. If no owner or no heartbeat -> notActivated
        # 2. If heartbeat is fresh -> online
        # 3. Otherwise -> offline
        
        is_activated = sa.and_(Worker.owner != None, Worker.last_heartbeat != None)
        is_fresh = (sa.sql.func.now() - Worker.last_heartbeat) < OFFLINE_THRESHOLD

        query = sa.select(
            # Total
            sa.sql.func.count(Worker.id).label("total"),
            
            # Dynamic Online Count (Must be activated AND heartbeat must be fresh)
            sa.sql.func.count(Worker.id).filter(
                sa.and_(is_activated, is_fresh)
            ).label("online"),
            
            # Busy Count (Usually only online workers can be busy)
            sa.sql.func.count(Worker.id).filter(
                sa.and_(is_activated, is_fresh, Worker.current_load > 0)
            ).label("busy"),
            
            # Total Jobs
            sa.sql.func.count(Job.id).label("total_jobs")
        ).select_from(Worker).join(
            Job, Worker.id == Job.worker_id, isouter=True
        ).where(
            Worker.project_id == project_id
        )

        result = await db.execute(query)
        stats = result.first()

        return {
            "total": stats.total or 0,
            "online": stats.online or 0,
            "busy": stats.busy or 0,
            "total_jobs": stats.total_jobs or 0
        }
    
    def get_all_worker_ids_by_project_id(self, project_id: int):
        workers = self._read_json()

        result = []
        for worker in workers:
            if worker["project_id"] == project_id:
                result.append(worker["id"])
        
        return result
    
    async def change_access_key(self, access_key_id: int, worker_id: int, db: AsyncSession):
        query = sa.select(Worker).where(Worker.id == worker_id)
        result = await db.execute(query)
        worker = result.scalar_one_or_none()
        isChange = False

        worker.access_key_id = access_key_id
        worker.status = WorkerStatus.NOT_ACTIVATE
        worker.is_active = False
        worker.last_heartbeat = None
        worker.internal_ip = None
        worker.hostname = None
        isChange = True
        
        await db.commit()
        await db.refresh(worker)

        if isChange: 
            return True
        return False
    
    async def disconnect_worker(self, worker_id: int, user_id: str, role: str, db: AsyncSession):
        query = sa.select(Worker).where(Worker.id == worker_id)
        result = await db.execute(query)
        worker_db = result.scalar_one_or_none()

        if not worker_db:
            raise HTTPException(status_code=404, detail="Worker not found")

        is_system_owner = (role == "owner")
        is_worker_owner = (worker_db.owner == user_id)

        if not (is_system_owner or is_worker_owner):
            raise HTTPException(
                status_code=403, 
                detail="Access denied: You do not have permission to manage this worker"
            )
        
        try:
            if worker_db.access_key_id:
                await access_key_service.delete_access_key_by_id(worker_db.access_key_id, db)
            
            new_key = await access_key_service.create_access_key(db)
                     
            worker_db.is_active = False
            worker_db.hostname = None
            worker_db.internal_ip = None
            worker_db.last_heartbeat = None
            worker_db.owner = None
            worker_db.status= WorkerStatus.NOT_ACTIVATE
            worker_db.access_key_id = new_key.id

            await db.commit()
            await db.refresh(worker_db)
            
            return worker_db
        
        except Exception as e:
            await db.rollback()
            print(f"Error resetting worker: {e}")
            raise HTTPException(status_code=500, detail="Failed to reset worker")

    async def disconnect_workers_in_project(self, project_id: int, db: AsyncSession):
        query = sa.select(Worker).where(Worker.project_id == project_id)
        result = await db.execute(query)
        rows = result.scalars().all()

        if not rows:
            raise HTTPException(status_code=404, detail="Worker not found")

        try:
            for worker in rows:
                if worker.access_key_id:
                    await access_key_service.delete_access_key_by_id(worker.access_key_id, db)
                
                new_key = await access_key_service.create_access_key(db)
                        
                worker.is_active = False
                worker.hostname = None
                worker.internal_ip = None
                worker.last_heartbeat = None
                worker.owner = None
                worker.status= WorkerStatus.NOT_ACTIVATE
                worker.access_key_id = new_key.id

            await db.commit()

            return {"message": f"Successfully disconnected {len(rows)} workers"}
            
        except Exception as e:
            await db.rollback()
            print(f"Error resetting worker: {e}")
            raise HTTPException(status_code=500, detail="Failed to reset worker")

    async def download_success(self, worker_id: int, user_id: str, db: AsyncSession):
        query = sa.select(Worker).where(Worker.id == worker_id)
        result = await db.execute(query)
        worker = result.scalar_one_or_none()

        worker.owner = user_id

        try:
            await db.commit()
            await db.refresh(worker) # This ensures all DB-generated fields are loaded

            return worker
        except Exception as e:
            await db.rollback()
            # Log the error so you can see it in the terminal
            print(f"Database Error: {e}") 
            raise HTTPException(status_code=500, detail="Internal Server Error")

    def verify_worker(self, req: VerifyRequest):
        workers = self._read_json()
        target_worker = None
        
        for worker in workers:
            if worker["id"] == req.worker_id:
                target_worker = worker

        if not target_worker.get("owner"):
            raise HTTPException(status_code=420, detail="Worker has no owner, cannot verify. Please download worker again to bind with your account.")

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
    
    async def update_heartbeat(self, worker_id: int, payload: HeartBeatPayload, db: AsyncSession):
        query = sa.select(Worker).where(Worker.id == worker_id)
        result = await db.execute(query)
        worker = result.scalar_one_or_none()

        if not worker:
            return False
        
        if not worker.owner:
            print("Worker has no owner, cannot verify")
            return False
        
        worker.current_load = payload.current_load
        worker.last_heartbeat = sa.sql.func.now()
        worker.status = payload.status
        worker.is_active = True
        worker.internal_ip = payload.internal_ip
        worker.hostname = payload.hostname

        
        try:
            await db.commit()
            await db.refresh(worker) # This ensures all DB-generated fields are loaded

            return True
        except Exception as e:
            await db.rollback()
            # Log the error so you can see it in the terminal
            print(f"Database Error: {e}") 
            raise HTTPException(status_code=500, detail="Internal Server Error")
            return False
    
    async def download_worker(self, worker_id: int, user_id: str, db: AsyncSession):
        """Service: download Worker"""
        query = sa.select(Worker).where(Worker.id == worker_id)
        result = await db.execute(query)
        worker_db = result.scalar_one_or_none()

        if not worker_db:
            raise HTTPException(status_code=404, detail="Worker not found")

        if worker_db.owner is not None:
            raise HTTPException(status_code=403, detail="Worker already has an owner, cannot download.")

        worker_db.owner = user_id

        try:
            await db.commit()
            await db.refresh(worker_db)

            hidden_payload = {
                "WORKER_ID": worker_id,
                "NUMBER_OF_THREADS": worker_db.thread_number,
                "BACKEND_URL": "http://127.0.0.1:8000",
                "REDIS_URL": settings.JOBS_REDIS_URL
            }


            EMBEDED_KEY = settings.EMBEDED_KEY.encode()
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

            dest_folder_name = f"SecurityWorker_{worker_db.name}"

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

        except Exception as e:
            await db.rollback()
            print(f"Error claiming worker: {e}")
            raise HTTPException(status_code=500, detail="Failed to assign worker")
        
    def read_all_worker(self, project_id: int):
        workers = self._read_json()
        result = []
        for w in workers:
            if w["project_id"] == project_id:
                result.append(w)

        return result


worker_service = WorkerService()