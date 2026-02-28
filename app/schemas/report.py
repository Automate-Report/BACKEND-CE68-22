from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class CreateReportPayload(BaseModel):
    asset_ids: Optional[List[int]] = []
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
