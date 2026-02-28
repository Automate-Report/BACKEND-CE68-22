# Lib imports
from pathlib import Path
from functools import partial
from reportlab.platypus import PageBreak, SimpleDocTemplate
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from collections import Counter

# Local imports
from Context import ReportContext
from PDFStyles import register_fonts, get_styles
from Layout import draw_page
from Sec00_Cover import create_cover_page
from Sec1_ExecutiveSummary import create_executive_summary
from Sec2_ScopeAndMethology import create_scope_and_methology
from Sec3_TechnicalFindings import create_technical_findings
from Sec4_VulnerabilityLifecycleTracking import create_vulnerability_lifecycle_tracking
from Sec5_Conclusion import create_conclusion
from SecA_AuditMethology import create_audit_methology
from SecB_RiskRating import create_risk_rating

# ==========================
# Initialize report context
# ==========================

context = ReportContext(
    # ==========================
    # Project Info
    # ==========================
    project_name="Example Project",

    # ==========================
    # Asset Info (primary display)
    # ==========================
    asset_name="example.com",

    # ==========================
    # Job Info
    # ==========================
    job_id="JOB-001",
    job_name="Example Job",
    job_started_date="01/01/2026",
    job_ended_date="05/01/2026",

    # ==========================
    # Scanner Info
    # ==========================
    scanner_name="My Security Scanner",
    support_email="support@example.com",
    efficiency=72.41,

    # ==========================
    # Placeholder (auto calculated)
    # ==========================
    total_vulns=0,
    total_asset=0,

    critical_cnt=0,
    high_cnt=0,
    medium_cnt=0,
    low_cnt=0,

    # ==========================
    # Assets
    # ==========================
    # Note: hc_cnt will be auto calc later (init = 0)
    assets=[
        {
            "asset_id": "AS-001",
            "asset_name": "example.com",
            "asset_desc": "Main production website.",
            "target": "https://example.com",
            "hc_cnt": 0,
            "status": "Open",
        },
        {
            "asset_id": "AS-002",
            "asset_name": "api.example.com",
            "asset_desc": "Public API server.",
            "target": "https://api.example.com",
            "hc_cnt": 0,
            "status": "Open",
        },
        {
            "asset_id": "AS-003",
            "asset_name": "192.168.1.10",
            "asset_desc": "Internal admin panel.",
            "target": "http://192.168.1.10",
            "hc_cnt": 0,
            "status": "Mitigated",
        },
    ],

    # ==========================
    # Vulnerabilities
    # ==========================
    vulns=[
        {
            "vuln_id": "V-001",
            "vuln_type": "SQL Injection",
            "severity": "Critical",
            "cvss_score": 9.8,
            "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
            "status": "Open",

            "dev_name": "John Doe",
            "tester_name": "Jane Smith",
            "asset_related": "AS-001",

            "target": "https://example.com/login",
            "parameter": "username",
            "description_from_library": "SQL Injection vulnerability detected.",

            "payload": "' OR '1'='1",
            "curl_command": "curl -X POST https://example.com/login",
            "evidence": "evidence/sql1.png",

            "reccommendation_from_library": "Use parameterized queries."
        },
        {
            "vuln_id": "V-002",
            "vuln_type": "Broken Access Control",
            "severity": "High",
            "cvss_score": 8.2,
            "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:N",
            "status": "Open",

            "dev_name": "Alice",
            "tester_name": "Bob",
            "asset_related": "AS-002",

            "target": "https://api.example.com/admin",
            "parameter": "N/A",
            "description_from_library": "Unauthorized access to admin endpoint.",

            "payload": "Direct URL access",
            "curl_command": "curl https://api.example.com/admin",
            "evidence": "evidence/bac.png",

            "reccommendation_from_library": "Implement role-based access control."
        },
        {
            "vuln_id": "V-003",
            "vuln_type": "Cross-Site Scripting (XSS)",
            "severity": "Medium",
            "cvss_score": 6.5,
            "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N",
            "status": "Mitigated",

            "dev_name": "Charlie",
            "tester_name": "Jane Smith",
            "asset_related": "AS-003",

            "target": "http://192.168.1.10/profile",
            "parameter": "name",
            "description_from_library": "Reflected XSS vulnerability.",

            "payload": "<script>alert(1)</script>",
            "curl_command": "curl http://192.168.1.10/profile?name=test",
            "evidence": "evidence/xss.png",

            "reccommendation_from_library": "Sanitize user input."
        },
    ]
)

# ==========================
# Auto Calculation Zone
# ==========================

# Total assets
context.total_asset = len(context.assets)

# Total vulnerabilities
context.total_vulns = len(context.vulns)

# Severity breakdown
severity_counter = Counter(v["severity"] for v in context.vulns)

context.critical_cnt = severity_counter.get("Critical", 0)
context.high_cnt = severity_counter.get("High", 0)
context.medium_cnt = severity_counter.get("Medium", 0)
context.low_cnt = severity_counter.get("Low", 0)

# Calculate High+Critical per asset
for vuln in context.vulns:
    if vuln["severity"] in ["Critical", "High"]:
        for asset in context.assets:
            if asset["asset_id"] == vuln["asset_related"]:
                asset["hc_cnt"] += 1

# ==========================
# Import Styles and Register Fonts
# ==========================
register_fonts("static/Fonts/")
styles = get_styles()

# ==========================
# Create document
# ==========================
# สร้าง Path โดยอ้างอิงจากตำแหน่งไฟล์ Python นี้ (Current Script Directory)
base_dir = Path(__file__).parent.parent.parent.parent.parent
file_path = base_dir / "fake_file_storage" / "report" / "penetration_testing_report.pdf"

# สร้างโฟลเดอร์ (สร้างซ้อนกันกี่ชั้นก็ได้ ถ้ามีอยู่แล้วก็ไม่ Error)
file_path.parent.mkdir(parents=True, exist_ok=True)

doc = SimpleDocTemplate(
    str(file_path),
    pagesize=A4,
    topMargin=28 * mm,   # space for header
    bottomMargin=20 * mm # space for footer
)

# ==========================
# Merge all pages
# ==========================
elements = []
elements += create_cover_page(context,styles)
elements.append(PageBreak())
elements += create_executive_summary(context, styles)
elements.append(PageBreak())
elements += create_scope_and_methology(context, styles)
elements.append(PageBreak())
elements += create_technical_findings(context, styles)
elements += create_vulnerability_lifecycle_tracking(context, styles)
elements.append(PageBreak())
elements += create_conclusion(context, styles)
elements.append(PageBreak())
elements += create_audit_methology(context, styles)
elements.append(PageBreak())
elements += create_risk_rating(context, styles)

# ==========================
# Build PDF
# ==========================
page_with_context = partial(draw_page, context)
doc.build(
    elements,
    onLaterPages=page_with_context
)
print("PDF generated successfully.")