from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Any
from datetime import datetime

class WorkerCreate(BaseModel):
    name: str
    thread_number: int


class WorkerResponse(BaseModel):
    id: int
    project_id: int
    access_key_id: Optional[int] = None
    owner: Optional[str] = None
    thread_number: int
    current_load: int 
    name: str
    hostname: Optional[str] = None
    internal_ip: Optional[str] = None
    status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_heartbeat: Optional[datetime] = None
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True # Allows you to create the model using either name
    )

class WorkerAccessKey(BaseModel):
    worker_id: int
    access_key_id: int

#-----------------Worker Agent----------------------#
class VerifyRequest(BaseModel):
    worker_id: int
    key: str
    hostname: str
    internal_ip: str

class HandshakeRequest(BaseModel):
    registration_token: str
    hostname: str

class HeartBeatPayload(BaseModel):
    current_load: int
    status: str
    internal_ip: str
    hostname: str

class AuthRequest(BaseModel):
    api_key: str
    
# Dummy
class TaskSubmitRequest(BaseModel):
    iteration: int
    status: str
    result: Optional[Any] = None #
