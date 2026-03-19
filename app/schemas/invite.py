from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

class InvitationResponse(BaseModel):
    project_id: int
    email: str
    project_name: str
    project_owner: str
    role: str
    status: str
    invited_at: datetime