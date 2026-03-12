from pathlib import Path
import asyncio
from collections import Counter
from playwright.async_api import async_playwright
import pdfplumber
from pdf2docx import Converter

from app.services.reports.gen_report.pdf_components import (
    sec_cover, sec_toc,
    sec1_executive_summary, sec2_scope,
    sec3_technical_findings, sec4_lifecycle,
    sec5_conclusion, appendix1, appendix2,
)

ANCHORS = {
    "sec1": "§ANCHOR§SEC1§",
    "sec2": "§ANCHOR§SEC2§",
    "sec3": "§ANCHOR§SEC3§",
    "sec4": "§ANCHOR§SEC4§",
    "sec5": "§ANCHOR§SEC5§",
    "app1": "§ANCHOR§APP1§",
    "app2": "§ANCHOR§APP2§",
}

class ReportContext:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

class GenerateReport:
    def __init__(self, context: ReportContext):
        self.context = context

    def _cal_cnt(self):
        self.context.total_asset  = len(self.context.assets)
        self.context.total_vulns  = len(self.context.vulns)
        sc = Counter(v["severity"] for v in self.context.vulns)
        self.context.critical_cnt = sc.get("Critical", 0)
        self.context.high_cnt     = sc.get("High", 0)
        self.context.medium_cnt   = sc.get("Medium", 0)
        self.context.low_cnt      = sc.get("Low", 0)
        for v in self.context.vulns:
            if v["severity"] in ["Critical", "High"]:
                for a in self.context.assets:
                    if a["asset_id"] == v["asset_related"]:
                        a["hc_cnt"] += 1

    def _build_html(self,page_nums: dict, include_anchors: bool = True) -> tuple[str, str]:
        content  = sec_cover(self.context)
        content += sec_toc(page_nums)
        content += sec1_executive_summary(self.context)
        content += sec2_scope(self.context)
        content += sec3_technical_findings(self.context)
        content += sec4_lifecycle(self.context)
        content += sec5_conclusion(self.context)
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

        base_dir = Path(__file__).resolve().parent
        template_path = base_dir / "pdf_base.html"
        with open(template_path, encoding="utf-8") as f:
            html = f.read().replace("{{ CONTENT }}", content)
        return html, base_dir
    
    def _read_page_numbers_from_pdf(self, pdf_path: str) -> dict:
        page_nums = {}
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                for key, marker in ANCHORS.items():
                    if marker in text and key not in page_nums:
                        page_nums[key] = page_num
        return page_nums
    
    async def _playwright_render(self, html: str, base_dir: str, output_path: str, browser):
        print(base_dir)
        tmp_html = base_dir / "_tmp_render.html"
        with open(tmp_html, "w", encoding="utf-8") as f:
            f.write(html)

        page = await browser.new_page()
        await page.goto(f"file:///{tmp_html.as_posix()}")
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
                f"<div style=\"font-size:12px; font-weight:700; color:#AAAAAA; margin-bottom: 2mm\">รายงานผลการทดสอบเจาะระบบ {self.context.asset_name}</div>"
                f"<div style=\"font-size:10px; font-weight:300; color:#DDDDDD; margin-bottom: 4mm\">หมายเลขเอกสาร: {self.context.job_name}</div>"
                "</div>"
            ),
            footer_template = """
                <div style="width:100%; font-family:sans-serif; font-size:8px;
                            color:#aaa; text-align:center;">
                — <span class="pageNumber"></span> —
                </div>""",
        )
        await page.close()

        tmp_html.unlink()

    async def _render_pdf(self):
        base_dir    = Path(__file__).resolve().parent.parent.parent.parent.parent
        pass1_path  = base_dir / "fake_file_storage" / "report" / f"{self.context.report_id}" / "_pass1.pdf"
        output_path = base_dir / "fake_file_storage" / "report" / f"{self.context.report_id}" / f"{self.context.report_name}.pdf"

        async with async_playwright() as p:
            browser = await p.chromium.launch()

            # ── Pass 1: gen PDF พร้อม anchor markers, TOC ยังไม่มีเลขหน้า ──
            print("📄 Pass 1: generating PDF with anchor markers...")
            html, base_dir = self._build_html(page_nums={}, include_anchors=True)
            await self._playwright_render(html, base_dir, pass1_path, browser)

            # ── อ่านเลขหน้าจาก PDF จริง ──
            print("🔍 Reading page numbers from PDF...")
            page_nums = self._read_page_numbers_from_pdf(pass1_path)
            print(f"   found: {page_nums}")
            pass1_path.unlink()

            # ── Pass 2: gen PDF อีกรอบพร้อมเลขหน้าใน TOC ──
            print("📄 Pass 2: generating final PDF with TOC page numbers...")
            html, base_dir = self._build_html(page_nums=page_nums, include_anchors=False)
            await self._playwright_render(html, base_dir, output_path, browser)

            await browser.close()

        print(f"✅ PDF saved → {output_path}")

    async def gen_report(self):
        await self._render_pdf()
        base_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
        pdf_path  = base_dir / "fake_file_storage" / "report" / f"{self.context.report_id}" / f"{self.context.report_name}.pdf"
        docx_path = base_dir / "fake_file_storage" / "report" / f"{self.context.report_id}" / f"{self.context.report_name}.docx"
        cv = Converter(pdf_path)
        cv.convert(docx_path)
        cv.close()
        print(f"✅ DOCX saved → {docx_path}")
        return pdf_path, docx_path
