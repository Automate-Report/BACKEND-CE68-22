from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

class WorkerCreate(BaseModel):
    name: str


class WorkerResponse(BaseModel):
    id: int
    name: str
    hostname: Optional[str] = None
    status: str
    isActive: bool
    access_key_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    last_heatbeat: Optional[datetime] = None

    class Config:
        orm_mode = True # เพื่อให้ Pydantic อ่านข้อมูลจาก ORM objects ได้ ไว้ใช้กับ SQLAlchemy ตอนทำ database

class WorkerAccessKey(BaseModel):
    worker_id: int
    access_key_id: int

#-----------------Worker Agent----------------------#
class VerifyRequest(BaseModel):
    key: str
    worker_id: int
    hostname: str

class HandshakeRequest(BaseModel):
    registration_token: str
    hostname: str

class AuthRequest(BaseModel):
    api_key: str
    
# Dummy
class TaskSubmitRequest(BaseModel):
    iteration: int
    status: str
    result: Optional[Any] = None #

#------------Pen Test Result-----------------------------#
class TargetInfo(BaseModel):
    url: str
    parameter: str
    method: str

# 2. ย่อย: Vuln Info
class VulnInfo(BaseModel):
    type: str
    severity: str
    db_type: Optional[str] = None
    xss_context: Optional[str] = None

# 3. ย่อย: Evidence
class EvidenceInfo(BaseModel):
    payload: str
    details: Optional[str] = ""
    screenshot: Optional[str] = None # Base64 String
    curl_command: Optional[str] = None

# 4. ย่อย: Technical
class TechnicalInfo(BaseModel):
    status_code: int
    request_headers: Optional[str] = ""
    response_headers: Optional[str] = ""
    timestamp: float

# 5. ย่อย: Remediation
class RemediationInfo(BaseModel):
    description: str
    recommendation: str

# --- MAIN SCHEMA (รับ JSON ก้อนใหญ่) ---
class FindingCreate(BaseModel):
    target: TargetInfo
    vulnerability: VulnInfo
    evidence: EvidenceInfo
    technical: TechnicalInfo
    remediation: RemediationInfo