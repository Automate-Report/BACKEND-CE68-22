from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from app.services.vulnerability import vuln_service

router = APIRouter()


# GET cnt of vuln using project_id
@router.get("cnt/{asset_ids}")
async def get_cnt_vulns_by_project_id(self, asset_ids: list):
    cnt = vuln_service.cnt_vuln_by_asset_id(asset_ids)
    return {
        "vuln_cnt": cnt
    }