import json
import os
import re
import base64

from datetime import datetime
from cvss import CVSS3
from typing import List

from app.schemas.pentest_log import FindingCreate


# 1. หา Path ของไฟล์ JSON (เพื่อให้รันได้ไม่ว่าจะอยู่ folder ไหน)
# app/services/project.py -> ขึ้นไป 3 ชั้นคือ root folder (backend)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSON_FILE_PATH = os.path.join(BASE_DIR, "dummy_data", "scan_findings.json")
PNG_FILE_PATH = os.path.join(BASE_DIR, "fake_file_storage", "img")

class ScanFindingService:
    
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
    
    def _sanitize_name(self, text):
        """ช่วยล้างชื่อ URL ให้เป็นชื่อไฟล์ที่ปลอดภัย"""
        return re.sub(r'[^a-zA-Z0-9]', '_', text.replace("http://", "").replace("https://", ""))

    def _base64_to_img(self, b64_string, url, job_id, vuln_id):
        #name file log_job_id_url_datetime
        if not b64_string:
            return None
            
        try:
            # 1. จัดเตรียมชื่อไฟล์: img_job_22_testphp_vulnweb_com_20260130_2015.png
            clean_url = self._sanitize_name(url)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"job_{job_id}_{clean_url}-{vuln_id}_{timestamp}.png"
            file_path = os.path.join(PNG_FILE_PATH, filename)

            # 2. แปลง Base64 เป็น Binary (ตัด Header "data:image/png;base64," ถ้ามี)
            if "," in b64_string:
                b64_string = b64_string.split(",")[1]
            
            img_data = base64.b64decode(b64_string)

            # 3. บันทึกไฟล์
            with open(file_path, "wb") as f:
                f.write(img_data)
            
            return file_path
        except Exception as e:
            print(f"❌ Error saving image: {e}")
            return None

    def create_batch_scan_findings(self, job_id: int, findings: List[FindingCreate]):
        scan_findings = self._read_json()
        new_records = []
        
        # ดึง ID ล่าสุดเพื่อรันต่อ
        last_id = scan_findings[-1]["id"] if scan_findings else 0

        for index, scan_finding in enumerate(findings):
            last_id += 1

            img_file = self._base64_to_img(scan_finding.evidence.screenshot, scan_finding.target.url, job_id, last_id)
            
            finding_record = {
                "id": last_id,
                "job_id": job_id, 
                "payload": scan_finding.evidence.payload,
                "screenshot_path": img_file,
                "curl_command": scan_finding.evidence.curl_command,
                "details": scan_finding.evidence.details,
                "timestamp": datetime.now().isoformat()
            }
            
            scan_findings.append(finding_record)
            new_records.append(finding_record)

        self._save_json(scan_findings)
        return new_records
    

scan_finding_service = ScanFindingService()