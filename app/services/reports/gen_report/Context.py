from dataclasses import dataclass
from multiprocessing import context

@dataclass
class ReportContext:
    assets: list[dict] # *1
    vulns: list[dict] # *2

    project_name: str
    
    total_asset: int
    asset_name: str

    job_id: str
    job_name: str
    job_started_date: str
    job_ended_date: str

    scanner_name: str
    support_email: str
    efficiency: float # x%

    total_vulns: int
    critical_cnt: int
    high_cnt: int
    medium_cnt: int
    low_cnt: int

# *1 minimum req of asset dictionary structure: (can send more than this but these are the required keys)
# {
#     "asset_id": "A-01",
#     "asset_name": "example.com",
#     "asset_desc": "description of the asset",
#     "target": "https://example.com",
#     "hc_cnt": 5, (high critical count)
#     "status": "status"
# }

# *2 minimum req of vuln dictionary structure: (can send more than this but these are the required keys)
# {
#     "vuln_id": "V-001",
#     "vuln_type": "SQL Injection",
#     "severity": "High",
#     "cvss_score": 7.5,
#     "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N",
#     "status": "Open",
#
#     "dev_name": "John Doe",
#     "tester_name": "Jane Smith",
#     "asset_related": "AUpixel.com",
#
#     "target": "https://example.com/vulnerable-endpoint",
#     "parameter": "id",
#     "description_from_library": "This is a description of the vulnerability from the library.",
#
#     "payload": "' OR '1'='1",
#     "curl_command": "curl -X GET 'https://example.com/vulnerable-endpoint?id=1'",
#     "evidence": "path/to/screenshot.png"
#
#     "reccommendation_from_library": "Recommended remediation steps from the vulnerability library.",
# }