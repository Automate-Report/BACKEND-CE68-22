from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from app.services.vulnerability import vuln_service
from app.services.asset import asset_service

router = APIRouter()


# GET cnt of vuln using project_id
@router.get("cnt/{project_id}")
async def get_cnt_vulns_by_project_id(project_id: int):
    asset_ids = asset_service.get_asset_ids_by_project_id(project_id)

    if not asset_ids:
        return {
            "vuln_cnt": 0
        }
    
    cnt = vuln_service.cnt_vuln_by_asset_id(asset_ids)
    return {
        "vuln_cnt": cnt
    }