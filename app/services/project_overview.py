
from datetime import datetime, timedelta, timezone
import zoneinfo

from sqlalchemy.ext.asyncio import AsyncSession

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.vulnerabilities import Vulnerability, VulnStatus, VulnSeverity
from app.models.projects import Project
from app.models.assets import Asset
from app.models.vuln_libs import VulnLib



class ProjectOverviewService:
    
    async def get_project_overview(self, project_id: int, db: AsyncSession):
        # 1. ดึงข้อมูลพื้นฐานโปรเจกต์
        project = (await db.execute(sa.select(Project).where(Project.id == project_id))).scalar_one_or_none()
        if not project: return None

        # 2. Aggregation Stats (Severity Counts)
        stats_query = (
            sa.select(
                sa.sql.func.count(Vulnerability.id).label("total_all"),
                sa.sql.func.count(Vulnerability.id).filter(Vulnerability.status == VulnStatus.OPEN).label("total_open"),
                sa.sql.func.count(Vulnerability.id).filter(Vulnerability.status == VulnStatus.FIXED).label("total_fixed"),
                sa.sql.func.count(Vulnerability.id).filter(sa.and_(Vulnerability.status == VulnStatus.OPEN, Vulnerability.severity == VulnSeverity.CRITICAL)).label("crit"),
                sa.sql.func.count(Vulnerability.id).filter(sa.and_(Vulnerability.status == VulnStatus.OPEN, Vulnerability.severity == VulnSeverity.HIGH)).label("high"),
                sa.sql.func.count(Vulnerability.id).filter(sa.and_(Vulnerability.status == VulnStatus.OPEN, Vulnerability.severity == VulnSeverity.MEDIUM)).label("med"),
                sa.sql.func.count(Vulnerability.id).filter(sa.and_(Vulnerability.status == VulnStatus.OPEN, Vulnerability.severity == VulnSeverity.LOW)).label("low"),
            )
            .join(Asset, Vulnerability.asset_id == Asset.id)
            .where(Asset.project_id == project_id)
        )
        stats_res = (await db.execute(stats_query)).first()

        # 3. คำนวณ Risk Score & Grade (สำหรับหน้า Header)
        risk_score = (stats_res.crit * 10) + (stats_res.high * 7) + (stats_res.med * 4) + (stats_res.low * 1)
        
        # 4. ดึงข้อมูลย่อย (Trend, Recent, Top Assets)
        trend = await self._get_sql_trend_data(project_id, db)
        recent = await self._get_sql_recent_findings(project_id, db)
        top_assets = await self._get_sql_top_risky_assets(project_id, db)

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
                "remediation_rate": f"{round(stats_res.total_fixed/stats_res.total_all*100, 1) if stats_res.total_all > 0 else 0}%",
                "severity_counts": {
                    "critical": stats_res.crit, "high": stats_res.high,
                    "medium": stats_res.med, "low": stats_res.low
                }
            },
            "top_risky_assets": top_assets,
            "trend": trend,
            "recent_vulnerabilities": recent
        }
    
    async def _get_sql_trend_data(self, project_id: int, db: AsyncSession):
        tz = zoneinfo.ZoneInfo("Asia/Bangkok")
        now = datetime.now(tz)
        trend = []
        for i in range(6, -1, -1):
            target_date = (now - timedelta(days=i)).date()
            print(target_date)
            
            # นับ Detected ในวันนั้น
            detected_query = (
                sa.select(sa.func.count(Vulnerability.id))
                .join(Asset, Vulnerability.asset_id == Asset.id)
                .where(
                    Asset.project_id == project_id,
                    sa.func.date(
                        Vulnerability.first_seen_at.op('AT TIME ZONE')('UTC').op('AT TIME ZONE')('Asia/Bangkok')
                    ) == target_date
                )
            )
            
            # 3. นับ Fixed: ทำแบบเดียวกันกับ resolved_at
            fixed_query = (
                sa.select(sa.func.count(Vulnerability.id))
                .join(Asset, Vulnerability.asset_id == Asset.id)
                .where(
                    Asset.project_id == project_id,
                    sa.func.date(
                        Vulnerability.resolved_at.op('AT TIME ZONE')('UTC').op('AT TIME ZONE')('Asia/Bangkok')
                    ) == target_date
                )
            )

            res_det = await db.execute(detected_query)
            detected_count = res_det.scalar() or 0

            res_fix = await db.execute(fixed_query)
            fixed_count = res_fix.scalar() or 0    # ดึงค่าออกมาครั้งเดียว

            # นำตัวแปรไปใช้ Print และ Append
            print(f"DEBUG: {target_date} - Detected: {detected_count}, Fixed: {fixed_count}")

            trend.append({
                "day": target_date.strftime("%a"),
                "date": target_date.isoformat(),
                "detected": detected_count,
                "fixed": fixed_count
            })
        return trend

    async def _get_sql_recent_findings(self, project_id, db):
        query = (
            sa.select(Vulnerability, VulnLib, Asset.name.label("asset_name"))
            .join(Asset, Vulnerability.asset_id == Asset.id)
            .join(VulnLib, Vulnerability.library_id == VulnLib.id, isouter=True) # Join เพื่อเอา CVE
            .where(sa.and_(Asset.project_id == project_id, Vulnerability.status == VulnStatus.OPEN))
            .order_by(sa.sql.desc(Vulnerability.first_seen_at))
            .limit(5)
        )
        rows = (await db.execute(query)).all()
        
        results = []
        now = datetime.now(timezone.utc)
        for v, lib, asset_name in rows:
            # คำนวณ SLA ตาม Severity
            sla_map = {"CRITICAL": 24, "HIGH": 72, "MEDIUM": 168, "LOW": 720}
            sev_name = v.severity.name.upper() if v.severity else "LOW"
            deadline = v.first_seen_at + timedelta(hours=sla_map.get(sev_name, 168))
            remaining = deadline - now

            results.append({
                "id": v.id,
                "title": lib.vuln_type if lib and lib.vuln_type else "Unknown Vulnerability",
                "cvss_score": lib.cvss_score if lib and lib.cvss_score else 0.0, # 👈 ต้องมี
                "severity": sev_name,
                "affected_asset": asset_name,
                "detected_at": self._time_ago(v.first_seen_at, now),
                "sla_status": self._format_sla(remaining), # 👈 ต้องมี
                "is_sla_breached": remaining.total_seconds() < 0
            })
        return results
    
    async def _get_sql_top_risky_assets(self, project_id, db):
        # ดึง Asset ที่มีช่องโหว่เยอะที่สุด 5 อันดับแรก
        query = (
            sa.select(
                Asset.id, Asset.name, 
                sa.sql.func.count(Vulnerability.id).label("v_count"),
                sa.sql.func.max(Vulnerability.severity).label("max_sev")
            )
            .join(Vulnerability, Asset.id == Vulnerability.asset_id)
            .where(sa.and_(Asset.project_id == project_id, Vulnerability.status == VulnStatus.OPEN))
            .group_by(Asset.id, Asset.name)
            .order_by(sa.sql.desc("v_count"))
            .limit(5)
        )
        res = (await db.execute(query)).all()
        return [{"id": r.id, "name": r.name, "vuln_count": r.v_count, "max_severity": r.max_sev.name.upper()} for r in res]

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