# =====================================================================
# generate.py  —  2-pass: gen PDF → อ่านเลขหน้าจาก PDF จริง → gen อีกรอบ
# =====================================================================
import os, asyncio
from collections import Counter
from playwright.async_api import async_playwright
import pdfplumber

from pdf_components import (
    sec_cover, sec_toc,
    sec1_executive_summary, sec2_scope,
    sec3_technical_findings, sec4_lifecycle,
    sec5_conclusion, appendix1, appendix2,
)

# ──────────────────────────────────────────────
# Context
# ──────────────────────────────────────────────
class ReportContext:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

context = ReportContext(
    report_name      = "report",
    project_name     = "Example Project",
    project_owner    = "Crafto Co. Ltd.",
    asset_name       = "example.com",
    job_id           = "JOB-001",
    job_name         = "Example Job",
    job_started_date = "01/01/2026",
    job_ended_date   = "05/01/2026",
    scanner_name     = "My Security Scanner",
    support_email    = "support@example.com",
    efficiency       = 72.41,
    total_vulns=0, total_asset=0,
    critical_cnt=0, high_cnt=0, medium_cnt=0, low_cnt=0,
    assets=[
        {"asset_id": "AS-001", "asset_name": "example.com",     "asset_desc": "Main production website.", "target": "https://example.com",    "hc_cnt": 0, "status": "Open"},
        {"asset_id": "AS-002", "asset_name": "api.example.com", "asset_desc": "Public API server.",       "target": "https://api.example.com", "hc_cnt": 0, "status": "Open"},
        {"asset_id": "AS-003", "asset_name": "192.168.1.10",    "asset_desc": "Internal admin panel.",    "target": "http://192.168.1.10",     "hc_cnt": 0, "status": "Mitigated"},
    ],
    vulns=[
        {"vuln_id": "V-001", "vuln_type": "SQL Injection",             "severity": "Critical", "cvss_score": 9.8, "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H", "status": "Open",      "dev_name": "John Doe", "tester_name": "Jane Smith", "asset_related": "AS-001", "target": "https://example.com/login",     "parameter": "username", "description_from_library": "SQL Injection vulnerability detected.", "payload": "' OR '1'='1",               "curl_command": "curl -X POST https://example.com/login",     "evidence": "", "reccommendation_from_library": "Use parameterized queries."},
        {"vuln_id": "V-002", "vuln_type": "Broken Access Control",     "severity": "High",     "cvss_score": 8.2, "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:N", "status": "Open",      "dev_name": "Alice",    "tester_name": "Bob",        "asset_related": "AS-002", "target": "https://api.example.com/admin", "parameter": "N/A",      "description_from_library": "Unauthorized access to admin endpoint.", "payload": "Direct URL access",         "curl_command": "curl https://api.example.com/admin",         "evidence": "", "reccommendation_from_library": "Implement role-based access control."},
        {"vuln_id": "V-003", "vuln_type": "Cross-Site Scripting (XSS)","severity": "Medium",   "cvss_score": 6.5, "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N", "status": "Mitigated", "dev_name": "Charlie",  "tester_name": "Jane Smith", "asset_related": "AS-003", "target": "http://192.168.1.10/profile",  "parameter": "name",     "description_from_library": "Reflected XSS vulnerability.",          "payload": "<script>alert(1)</script>", "curl_command": "curl http://192.168.1.10/profile?name=test", "evidence": "", "reccommendation_from_library": "Sanitize user input."},
    ]
)

# Auto calc
context.total_asset  = len(context.assets)
context.total_vulns  = len(context.vulns)
sc = Counter(v["severity"] for v in context.vulns)
context.critical_cnt = sc.get("Critical", 0)
context.high_cnt     = sc.get("High", 0)
context.medium_cnt   = sc.get("Medium", 0)
context.low_cnt      = sc.get("Low", 0)
for v in context.vulns:
    if v["severity"] in ["Critical", "High"]:
        for a in context.assets:
            if a["asset_id"] == v["asset_related"]:
                a["hc_cnt"] += 1

# ──────────────────────────────────────────────
# Anchor markers — ฝังไว้ใน PDF เพื่ออ่านภายหลัง
# key ต้องไม่ซ้ำและ unique พอที่จะ search เจอ
# ──────────────────────────────────────────────
ANCHORS = {
    "sec1": "§ANCHOR§SEC1§",
    "sec2": "§ANCHOR§SEC2§",
    "sec3": "§ANCHOR§SEC3§",
    "sec4": "§ANCHOR§SEC4§",
    "sec5": "§ANCHOR§SEC5§",
    "app1": "§ANCHOR§APP1§",
    "app2": "§ANCHOR§APP2§",
}

# ──────────────────────────────────────────────
# Build HTML
# ──────────────────────────────────────────────
def build_html(page_nums: dict, include_anchors: bool = True) -> tuple[str, str]:
    content  = sec_cover(context)
    content += sec_toc(page_nums)
    content += sec1_executive_summary(context)
    content += sec2_scope(context)
    content += sec3_technical_findings(context)
    content += sec4_lifecycle(context)
    content += sec5_conclusion(context)
    content += appendix1()
    content += appendix2()

    # ฝัง anchor text แบบซ่อน (สีขาว ขนาด 1px) ไว้ต้นแต่ละ section
    if include_anchors:
        for key, marker in ANCHORS.items():
            content = content.replace(
                f'<div data-anchor="{key}"></div>',
                f'<div data-anchor="{key}"></div>'
                f'<span style="font-size:1px;color:white;position:absolute;">{marker}</span>'
            )

    base_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(base_dir, "pdf_base.html"), encoding="utf-8") as f:
        html = f.read().replace("{{ CONTENT }}", content)
    return html, base_dir


# ──────────────────────────────────────────────
# อ่านเลขหน้าจาก PDF จริง ด้วย pdfplumber
# ──────────────────────────────────────────────
def read_page_numbers_from_pdf(pdf_path: str) -> dict:
    page_nums = {}
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            for key, marker in ANCHORS.items():
                if marker in text and key not in page_nums:
                    page_nums[key] = page_num
    return page_nums


# ──────────────────────────────────────────────
# Playwright render helper
# ──────────────────────────────────────────────
async def playwright_render(html: str, base_dir: str, output_path: str, browser):
    tmp_html = os.path.join(base_dir, "_tmp_render.html")
    with open(tmp_html, "w", encoding="utf-8") as f:
        f.write(html)

    page = await browser.new_page()
    await page.goto(f"file:///{tmp_html.replace(chr(92), '/')}")
    await page.wait_for_load_state("networkidle")
    await page.pdf(
        path    = output_path,
        format  = "A4",
        margin  = {"top": "10mm","bottom": "22mm", "left": "20mm", "right": "20mm"},
        print_background      = True,
        display_header_footer = True,
        header_template = (
            "<div style=\"width:80%; font-family:sans-serif;"
            "margin: 8px 10mm 8px 10mm; border-bottom: 0.5px solid #EEEEEE\">"
            f"<div style=\"font-size:12px; font-weight:700; color:#AAAAAA; margin-bottom: 2mm\">รายงานผลการทดสอบเจาะระบบ {context.asset_name}</div>"
            f"<div style=\"font-size:10px; font-weight:300; color:#DDDDDD; margin-bottom: 4mm\">หมายเลขเอกสาร: {context.job_name}</div>"
            "</div>"
        ),
        footer_template = """
            <div style="width:100%; font-family:sans-serif; font-size:8px;
                        color:#aaa; text-align:center;">
              — <span class="pageNumber"></span> —
            </div>""",
    )
    await page.close()
    os.remove(tmp_html)


# ──────────────────────────────────────────────
# Main: 2-pass render
# ──────────────────────────────────────────────
async def render_pdf():
    base_dir    = os.path.dirname(os.path.abspath(__file__))
    pass1_path  = os.path.join(base_dir, "_pass1.pdf")
    output_path = os.path.join(base_dir, "output.pdf")

    async with async_playwright() as p:
        browser = await p.chromium.launch()

        # ── Pass 1: gen PDF พร้อม anchor markers, TOC ยังไม่มีเลขหน้า ──
        print("📄 Pass 1: generating PDF with anchor markers...")
        html, base_dir = build_html(page_nums={}, include_anchors=True)
        await playwright_render(html, base_dir, pass1_path, browser)

        # ── อ่านเลขหน้าจาก PDF จริง ──
        print("🔍 Reading page numbers from PDF...")
        page_nums = read_page_numbers_from_pdf(pass1_path)
        print(f"   found: {page_nums}")
        os.remove(pass1_path)

        # ── Pass 2: gen PDF อีกรอบพร้อมเลขหน้าใน TOC ──
        print("📄 Pass 2: generating final PDF with TOC page numbers...")
        html, base_dir = build_html(page_nums=page_nums, include_anchors=False)
        await playwright_render(html, base_dir, output_path, browser)

        await browser.close()

    print(f"✅ PDF saved → {output_path}")


if __name__ == "__main__":
    asyncio.run(render_pdf())

    from pdf2docx import Converter
    base_dir  = os.path.dirname(os.path.abspath(__file__))
    pdf_path  = os.path.join(base_dir, "output.pdf")
    docx_path = os.path.join(base_dir, "output.docx")
    cv = Converter(pdf_path)
    cv.convert(docx_path)
    cv.close()
    print(f"✅ DOCX saved → {docx_path}")