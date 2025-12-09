from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.schemas.agent import WorkerCreate, WorkerResponse
from app.services.agent import worker_service
import zipfile
import io
import json
import uuid
import datetime
from typing import Dict, List

router = APIRouter()
# --- Mock Database ---
# เก็บ Token ชั่วคราว: {"token_xxx": {"expires": datetime, "user_id": "user_1"}}
setup_tokens = {} 
# เก็บ Agent ที่ลงทะเบียนแล้ว: {"agent_key_xxx": {"status": "online", "last_seen": ...}}
registered_agents = {}
# คิวงาน: [{"id": 1, "target": "...", "type": "sqli", "status": "pending"}]
job_queue = []
# ผลลัพธ์งาน
scan_results = []


# Create Worker Endpoints
# POST /workers/ : สร้าง Worker ใหม่
@router.post("/", response_model=WorkerResponse)
async def create_worker(worker_in: WorkerCreate):
    new_worker = worker_service.create_worker(worker_in)
    return new_worker

# Download Agent Endpoint
@router.post("/api/download-agent")
async def download_agent():
    # สร้าง Setup Token (อายุสั้น)
    token = str(uuid.uuid4())
    setup_tokens[token] = {
        "expires": datetime.datetime.now() + datetime.timedelta(minutes=10),
        "user_label": f"User_{token[:4]}"
    }

    # สร้างไฟล์ Config
    config_data = {
        "server_url": "http://localhost:8000",
        "setup_token": token
    }
    
    # อ่านไฟล์ Agent ต้นฉบับ (ในที่นี้สมมติว่าอ่านจากไฟล์ source)
    # ในการใช้งานจริง ควรเป็นไฟล์ .exe ที่ Compile ไว้แล้ว
    try:
        with open("agent_source.py", "r", encoding="utf-8") as f:
            agent_code = f.read()
    except FileNotFoundError:
        agent_code = "# Agent source code not found on server"

    # สร้าง Zip ใน Memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zf:
        zf.writestr("config.json", json.dumps(config_data, indent=4))
        zf.writestr("agent_run.py", agent_code) # ของจริงจะเป็น agent.exe
        zf.writestr("README.txt", "Double click agent_run.py to start.")

    zip_buffer.seek(0)
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=agent_{token[:4]}.zip"}
    )

# --- 2. Agent ลงทะเบียน (แลก Token เป็น Key ถาวร) ---
@router.post("/api/register")
async def register_agent(payload: dict):
    token = payload.get("setup_token")
    
    # ตรวจสอบ Token
    if token not in setup_tokens:
        raise HTTPException(400, "Invalid or expired token")
    
    # สร้าง Key ถาวรใหม่
    real_agent_key = str(uuid.uuid4())
    registered_agents[real_agent_key] = {
        "user": setup_tokens[token]["user_label"],
        "status": "online"
    }
    
    # ลบ Token เก่าทิ้งทันที (Security)
    del setup_tokens[token]
    
    return {"access_key": real_agent_key}