from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from app.schemas.vulnerability import SummaryCntVlun

from app.services.vulnerability import vuln_service
from app.services.asset import asset_service

router = APIRouter()


# GET cnt of vuln using project_id
@router.get("/cnt/{project_id}")
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

@router.get("/summary/vuln/{project_id}", response_model=SummaryCntVlun)
async def get_summary_vuln_by_project_id(project_id: int):
    asset_ids = asset_service.get_asset_ids_by_project_id(project_id)

    if not asset_ids:
        return SummaryCntVlun(
            total=0,
            open_cnt=0,
            tp_cnt=0,
            in_progress_cnt=0,
            fixed_cnt=0
        )
    
    result = SummaryCntVlun(
        total=0,
        open_cnt=0,
        tp_cnt=0,
        in_progress_cnt=0,
        fixed_cnt=0
    )
    
    for id in asset_ids:
        value = vuln_service.cnt_status_vuln_by_asset_id(id)

        result.total+=value.total
        result.open_cnt+=value.open_cnt
        result.tp_cnt+=value.tp_cnt
        result.in_progress_cnt+=value.in_progress_cnt
        result.fixed_cnt+=value.fixed_cnt

    return result
    
