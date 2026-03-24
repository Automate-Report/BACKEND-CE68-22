import json
import os
import math

from datetime import datetime, timedelta, timezone
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.vulnerabilities import Vulnerability, VulnStatus, VulnSeverity
from app.models.projects import Project
from app.models.assets import Asset
from app.models.vuln_libs import VulnLib

# 1. หา Path ของไฟล์ JSON (เพื่อให้รันได้ไม่ว่าจะอยู่ folder ไหน)
# app/services/project.py -> ขึ้นไป 3 ชั้นคือ root folder (backend)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSON_FILE_PATH = os.path.join(BASE_DIR, "dummy_data", "projects.json")

class ProjectOverviewService:
    
    async def get_project_overview(self, project_id: int, db: AsyncSession):
        # 1. ตรวจสอบว่าโปรเจกต์มีอยู่จริง
        project_query = sa.select(Project).where(Project.id == project_id)
        project = (await db.execute(project_query)).scalar_one_or_none()
        if not project:
            return None

        # 2. คำนวณสถิติภาพรวม (Severity Counts & Total Vulns) ใน Query เดียว
        # เราจะกรองเฉพาะช่องโหว่ที่อยู่ใน Asset ของโปรเจกต์นี้
        stats_query = (
            sa.select(
                sa.sql.func.count(Vulnerability.id).label("total_all"),
                sa.sql.func.count(Vulnerability.id).filter(Vulnerability.status == VulnStatus.OPEN).label("total_open"),
                sa.sql.func.count(Vulnerability.id).filter(Vulnerability.status == VulnStatus.FIXED).label("total_fixed"),
                # นับแยกตาม Severity
                sa.sql.func.count(Vulnerability.id).filter(sa.and_(Vulnerability.status == VulnStatus.OPEN, Vulnerability.severity == VulnSeverity.CRITICAL)).label("crit"),
                sa.sql.func.count(Vulnerability.id).filter(sa.and_(Vulnerability.status == VulnStatus.OPEN, Vulnerability.severity == VulnSeverity.HIGH)).label("high"),
                sa.sql.func.count(Vulnerability.id).filter(sa.and_(Vulnerability.status == VulnStatus.OPEN, Vulnerability.severity == VulnSeverity.MEDIUM)).label("med"),
                sa.sql.func.count(Vulnerability.id).filter(sa.and_(Vulnerability.status == VulnStatus.OPEN, Vulnerability.severity == VulnSeverity.LOW)).label("low"),
            )
            .join(Asset, Vulnerability.asset_id == Asset.id)
            .where(Asset.project_id == project_id)
        )
        
        stats_res = (await db.execute(stats_query)).first()
        
        # คำนวณ Risk Score
        risk_score = (stats_res.crit * 10) + (stats_res.high * 7) + (stats_res.med * 4) + (stats_res.low * 1)
        remediation_rate = round((stats_res.total_fixed / stats_res.total_all * 100), 1) if stats_res.total_all > 0 else 0

        # 3. ดึง Trend 7 วันล่าสุด (Detected vs Fixed)
        trend_data = await self._get_sql_trend_data(project_id, db)

        # 4. Top Risky Assets (Asset ที่มีช่องโหว่ OPEN เยอะที่สุด)
        top_assets_query = (
            sa.select(Asset.id, Asset.name, sa.sql.func.count(Vulnerability.id).label("v_count"))
            .join(Vulnerability, Asset.id == Vulnerability.asset_id)
            .where(sa.and_(Asset.project_id == project_id, Vulnerability.status == VulnStatus.OPEN))
            .group_by(Asset.id, Asset.name)
            .order_by(sa.sql.desc("v_count"))
            .limit(5)
        )
        top_assets_res = (await db.execute(top_assets_query)).all()

        # 5. Recent Vulnerabilities (5 รายการล่าสุด)
        recent_vulns = await self._get_sql_recent_findings(project_id, db)

        return {
            "project_info": {
                "id": project.id,
                "name": project.name,
                "risk_grade": self._get_risk_grade(risk_score),
                "risk_score": round(risk_score, 1)
            },
            "stats": {
                "total_assets": await self._count_assets(project_id, db),
                "vulns_total": stats_res.total_open,
                "remediation_rate": f"{remediation_rate}%",
                "severity_counts": {
                    "critical": stats_res.crit,
                    "high": stats_res.high,
                    "medium": stats_res.med,
                    "low": stats_res.low
                }
            },
            "top_risky_assets": [
                {"id": r.id, "name": r.name, "vuln_count": r.v_count, "max_severity": "HIGH"} # เพิ่ม Logic เช็ค Max Severity ได้ถ้าต้องการ
                for r in top_assets_res
            ],
            "trend": trend_data,
            "recent_vulnerabilities": recent_vulns
        }
    
    async def _get_sql_trend_data(self, project_id: int, db: AsyncSession):
        now = datetime.now(timezone.utc)
        trend = []
        for i in range(6, -1, -1):
            target_date = (now - timedelta(days=i)).date()
            
            # นับ Detected ในวันนั้น
            detected = await db.execute(sa.select(sa.sql.func.count(Vulnerability.id))
                .join(Asset, Vulnerability.asset_id == Asset.id)
                .where(sa.and_(Asset.project_id == project_id, sa.cast(Vulnerability.first_seen_at, sa.Date) == target_date)))
            
            # นับ Fixed ในวันนั้น (เช็คจาก resolved_at ที่เราทำ Event Listener ไว้)
            fixed = await db.execute(sa.select(sa.sql.func.count(Vulnerability.id))
                .join(Asset, Vulnerability.asset_id == Asset.id)
                .where(sa.and_(Asset.project_id == project_id, sa.cast(Vulnerability.resolved_at, sa.Date) == target_date)))

            trend.append({
                "day": target_date.strftime("%a"),
                "date": target_date.isoformat(),
                "detected": detected.scalar() or 0,
                "fixed": fixed.scalar() or 0
            })
        return trend

    async def _get_sql_recent_findings(self, project_id, db):
        query = (
            sa.select(Vulnerability, VulnLib, Asset.name.label("asset_name"))
            .join(Asset, Vulnerability.asset_id == Asset.id)
            .join(VulnLib, Vulnerability.library_id == VulnLib.id, isouter=True)
            .where(sa.and_(Asset.project_id == project_id, Vulnerability.status == VulnStatus.OPEN))
            .order_by(sa.sql.desc(Vulnerability.first_seen_at))
            .limit(5)
        )
        rows = (await db.execute(query)).all()
        
        results = []
        now = datetime.now(timezone.utc)
        for v, lib, asset_name in rows:
            # 1. คำนวณ SLA (ดักกรณี v.severity เป็น None)
            sev_name = v.severity.name.upper() if v.severity else "LOW"
            sla_hours = {"CRITICAL": 24, "HIGH": 72, "MEDIUM": 168, "LOW": 720}
            
            # 2. ตรวจสอบเวลา first_seen_at (ถ้าใน DB เป็น Null ให้ใช้เวลาปัจจุบันแทน)
            base_time = v.first_seen_at if v.first_seen_at else now
            deadline = base_time + timedelta(hours=sla_hours.get(sev_name, 168))
            remaining = deadline - now

            results.append({
                "id": v.id,
                "title": (lib.vuln_type[0] if lib and lib.vuln_type else "Unknown Vulnerability"),
                "cve": (lib.cve_id if lib and lib.cve_id else "N/A"), # ✅ ป้องกัน Error 'cve' missing
                "cvss_score": (lib.cvss_score if lib and lib.cvss_score else 0.0), # ✅ ป้องกัน missing
                "severity": sev_name,
                "affected_asset": asset_name or "Unknown Asset",
                "detected_at": self._time_ago(base_time, now),
                "sla_status": self._format_sla(remaining), # ✅ ฟังก์ชันที่เราเพิ่งเพิ่มไป
                "is_sla_breached": remaining.total_seconds() < 0
            })
        return results

    async def _count_assets(self, project_id, db):
        res = await db.execute(sa.select(sa.sql.func.count(Asset.id)).where(Asset.project_id == project_id))
        return res.scalar() or 0
    
    def _time_ago(self, dt, now):
        """แปลง DateTime เป็นข้อความว่าผ่านมานานแค่ไหนแล้ว"""
        if not dt:
            return "Unknown"
        
        diff = now - dt
        
        if diff.total_seconds() < 60:
            return "Just now"
        if diff.total_seconds() < 3600:
            return f"{int(diff.total_seconds() // 60)}m ago"
        if diff.days < 1:
            return f"{int(diff.total_seconds() // 3600)}h ago"
        if diff.days < 30:
            return f"{diff.days}d ago"
        
        return dt.strftime("%Y-%m-%d")

    def _get_risk_grade(self, score: float) -> str:
        """แปลงคะแนนความเสี่ยงเป็นเกรด A+ ถึง D"""
        if score == 0: 
            return "A+"
        if score < 15: 
            return "A"
        if score < 40: 
            return "B"
        if score < 80: 
            return "C"
        return "D"

    def _format_sla(self, diff):
        """ฟอร์แมตเวลา SLA ที่เหลือให้เป็นข้อความอ่านง่าย"""
        if diff.total_seconds() < 0: 
            return "OVERDUE"
        hours = int(diff.total_seconds() // 3600)
        if hours < 48:
            return f"{hours}h left"
        return f"{diff.days}d left"
  

# สร้าง Instance ไว้ให้ Router เรียกใช้
project_overview_service = ProjectOverviewService()