from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Literal
from datetime import datetime

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    tag_ids: Optional[List[int]] = []

class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    role: str = "owner"
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True # เพื่อให้ Pydantic อ่านข้อมูลจาก ORM objects ได้ ไว้ใช้กับ SQLAlchemy ตอนทำ database
        orm_mode = True # เพื่อให้ Pydantic อ่านข้อมูลจาก ORM objects ได้ ไว้ใช้กับ SQLAlchemy ตอนทำ database

class Tag(BaseModel):
    name: str
    text_color: str
    bg_color: str

    model_config = ConfigDict(from_attributes=True)

class ProjectSummaryResponese(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    role: Literal["owner", "pentester", "developer"]
    assets_cnt: int
    vuln_cnt: int
    tags: Optional[List[Tag]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class RecentVulnerability(BaseModel):
    id: int
    title: str
    cve: str
    severity: str
    cvss_score: float
    affected_asset: str
    detected_at: str  # เช่น "2 hours ago"
    sla_status: str   # เช่น "18h left" หรือ "OVERDUE"
    is_sla_breached: bool


#------------------------------- สำหรับ Project Overview ----------------------------------
class ProjectOverviewInfo(BaseModel):
    id: int
    name: str
    risk_grade: str
    risk_score: float

class ProjectStats(BaseModel):
    total_assets: int
    vulns_total: int # เปลี่ยนจาก total_vulns
    remediation_rate: str # เปลี่ยนจาก float เป็น str เพราะมีเครื่องหมาย %
    severity_counts: Dict[str, int]

class ProjectAssetOverview(BaseModel):
    id: int
    name: str
    vuln_count: int
    max_severity: str

class ProjectTrendData(BaseModel):
    day: str
    date: datetime
    detected: int
    fixed: int

class ProjectOverviewResponse(BaseModel):
    project_info: ProjectOverviewInfo
    stats: ProjectStats
    top_risky_assets: List[ProjectAssetOverview]
    trend: List[ProjectTrendData]
    recent_vulnerabilities: List[RecentVulnerability]


#------------------------------- สำหรับ Project Member Management ----------------------------------
class ProjectMemberResponse(BaseModel):
    project_id: int
    email: str
    role: str
    status: str
    joinned_at: Optional[datetime] = None
    invited_at: datetime