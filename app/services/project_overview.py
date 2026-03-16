import json
import os

from datetime import datetime, timedelta, timezone
from typing import List

from app.services.project import project_service
from app.services.asset import asset_service
from app.services.vulnerability import vuln_service

# 1. หา Path ของไฟล์ JSON (เพื่อให้รันได้ไม่ว่าจะอยู่ folder ไหน)
# app/services/project.py -> ขึ้นไป 3 ชั้นคือ root folder (backend)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSON_FILE_PATH = os.path.join(BASE_DIR, "dummy_data", "projects.json")

class ProjectOverviewService:
    
    def _ensure_dummy_folder_exists(self):
        """ตรวจสอบว่ามี folder dummy_data หรือยัง ถ้าไม่มีให้สร้าง"""
        folder = os.path.dirname(JSON_FILE_PATH)
        if not os.path.exists(folder):
            os.makedirs(folder)

    def _read_json(self) -> List[dict]:
        """อ่านข้อมูลจากไฟล์ JSON"""
        if not os.path.exists(JSON_FILE_PATH):
            return []
        try:
            with open(JSON_FILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return [] # ถ้าไฟล์เสียหรือว่างเปล่า ให้คืนค่า list ว่าง

    def _save_json(self, data: List[dict]):
        """บันทึกข้อมูลลงไฟล์ JSON"""
        self._ensure_dummy_folder_exists()
        with open(JSON_FILE_PATH, "w", encoding="utf-8") as f:
            # default=str ช่วยแปลง datetime เป็น string อัตโนมัติ
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    def _get_recent_findings(self, open_vulns, assets, libs, limit=5):
        # สร้าง Map เพื่อความเร็วในการค้นหา
        asset_map = {a["id"]: a["name"] for a in assets}
        lib_map = {l["id"]: l for l in libs}
        
        # เรียงตามวันล่าสุด
        sorted_vulns = sorted(open_vulns, key=lambda x: x.get("first_seen_at", ""), reverse=True)
        
        results = []
        now = datetime.now(timezone.utc)
        
        for v in sorted_vulns[:limit]:
            lib = lib_map.get(v.get("library_id"), {})
            
            # ดึงค่าวันที่มาตรวจสอบ
            raw_date = v.get("first_seen_at")
            if not raw_date:
                continue

            # ✅ แปลงให้เป็น Aware แน่นอนโดยการแทนที่ Z ด้วย +00:00
            # หากข้อมูลไม่มี Z ให้ใช้ .astimezone(timezone.utc) กำกับท้าย
            try:
                dt_obj = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
                if dt_obj.tzinfo is None:
                    dt_obj = dt_obj.replace(tzinfo=timezone.utc)
                first_seen = dt_obj
            except Exception:
                continue
            
            # คำนวณ SLA
            sla_hours = {"critical": 24, "high": 72, "medium": 168, "low": 720}
            deadline = first_seen + timedelta(hours=sla_hours.get(v.get("severity", "low").lower(), 168))
            
            # ✅ บรรทัดที่ 63: ตอนนี้ทั้งคู่เป็น Aware แล้ว (มี tzinfo ทั้งคู่)
            remaining = deadline - now
            
            results.append({
                "id": v["id"],
                "title": lib.get("vuln_type", "Unknown"),
                "cve": lib.get("cve_id", "N/A"),
                "severity": v["severity"].upper(),
                "cvss_score": lib.get("cvss_score", 0.0),
                "affected_asset": asset_map.get(v["asset_id"], "Unknown"),
                "detected_at": self._time_ago(first_seen, now),
                "sla_status": self._format_sla(remaining),
                "is_sla_breached": remaining.total_seconds() < 0
            })
        return results

    def _time_ago(self, dt, now):
        diff = now - dt
        if diff.seconds < 3600: return f"{diff.seconds // 60}m ago"
        if diff.days < 1: return f"{diff.seconds // 3600}h ago"
        return f"{diff.days}d ago"

    def _format_sla(self, diff):
        if diff.total_seconds() < 0: return "OVERDUE"
        hours = int(diff.total_seconds() // 3600)
        return f"{hours}h left" if hours < 48 else f"{diff.days}d left"

    def _get_risk_grade(self, score):
        if score == 0: return "A+"
        if score < 15: return "A"
        if score < 40: return "B"
        if score < 80: return "C"
        return "D"

    def _calculate_top_risky_assets(self, assets, open_vulns):
        risky_list = []
        for a in assets:
            v_count = len([v for v in open_vulns if v["asset_id"] == a["id"]])
            if v_count > 0:
                risky_list.append({
                    "id": a["id"], 
                    "name": a["name"], 
                    "vuln_count": v_count,
                    "max_severity": "CRITICAL" if any(v["severity"] == "critical" for v in open_vulns if v["asset_id"] == a.get("id")) else "HIGH"
                })
        return sorted(risky_list, key=lambda x: x["vuln_count"], reverse=True)[:5]

    def _get_actual_trend_data(self, project_vulns):
        trend = []
        now = datetime.now(timezone.utc)
        
        # คำนวณย้อนหลัง 7 วัน
        for i in range(6, -1, -1):
            target_date = (now - timedelta(days=i)).date()
            day_name = target_date.strftime("%a") # เช่น Mon, Tue
            
            # 1. นับช่องโหว่ที่ "ตรวจพบ" ในวันนั้น (Detected)
            detected_count = 0
            for v in project_vulns:
                raw_seen = v.get("first_seen_at")
                if raw_seen:
                    v_date = datetime.fromisoformat(raw_seen.replace("Z", "+00:00")).date()
                    if v_date == target_date:
                        detected_count += 1
            
            # 2. นับช่องโหว่ที่ "แก้ไขเสร็จ" ในวันนั้น (Fixed)
            # ต้องเช็ค status == "fixed" และ updated_at ตรงกับวันที่เป้าหมาย
            fixed_count = 0
            for v in project_vulns:
                if v.get("status") == "fixed" and v.get("updated_at"):
                    f_date = datetime.fromisoformat(v["updated_at"].replace("Z", "+00:00")).date()
                    if f_date == target_date:
                        fixed_count += 1
            
            trend.append({
                "day": day_name,
                "date": target_date.isoformat(),
                "detected": detected_count,
                "fixed": fixed_count
            })
            
        return trend
    
    def get_project_overview(self, project_id: int):

        project = project_service.get_project_by_id(project_id)
        if not project:
            return None
        
        assets = asset_service.get_assets_by_project_id(project_id)

        vulns = []
        for asset in assets:
            vulns.extend(vuln_service.get_vulns_by_asset_id(asset["id"]))

        libs = vuln_service.get_vuln_library()

        open_vulns = [v for v in vulns if v.get("status") == "open"]
        fixed_vulns = [v for v in vulns if v.get("status") == "fixed"]

        severity_stats = {
            "critical": len([v for v in open_vulns if v.get("severity") == "critical"]),
            "high": len([v for v in open_vulns if v.get("severity") == "high"]),
            "medium": len([v for v in open_vulns if v.get("severity") == "medium"]),
            "low": len([v for v in open_vulns if v.get("severity") == "low"])
        }

        # 3. Risk Scoring (Weighted Score)
        # Formula: Crit*10 + High*7 + Med*4 + Low*1
        risk_score = (severity_stats["critical"] * 10) + (severity_stats["high"] * 7) + \
                     (severity_stats["medium"] * 4) + (severity_stats["low"] * 1)
        
        # 4. Recent Vulnerabilities (New Findings)
        recent_findings = self._get_recent_findings(open_vulns, assets, libs)

        # 5. Top Risky Assets
        top_assets = self._calculate_top_risky_assets(assets, open_vulns)

        return {
            "project_info": {
                "id": project["id"],
                "name": project["name"],
                "risk_grade": self._get_risk_grade(risk_score),
                "risk_score": round(risk_score, 1)
            },
            "stats": {
                "total_assets": len(assets),
                "vulns_total": len(open_vulns),
                "remediation_rate": f"{round(len(fixed_vulns)/len(vulns)*100, 1) if vulns else 0}%",
                "severity_counts": severity_stats
            },
            "top_risky_assets": top_assets,
            "trend": self._get_actual_trend_data(vulns), # สามารถเปลี่ยนเป็น Logic ดึงข้อมูลจริงได้
            "recent_vulnerabilities": recent_findings
        }


  

# สร้าง Instance ไว้ให้ Router เรียกใช้
project_overview_service = ProjectOverviewService()