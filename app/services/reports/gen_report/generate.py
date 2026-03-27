import asyncio
import pdfplumber

from pathlib import Path
from pdf2docx import Converter
from collections import Counter
from playwright.sync_api import sync_playwright
from concurrent.futures import ThreadPoolExecutor

from app.services.reports.gen_report.pdf_components import (
    sec_cover, sec_toc,
    sec1_executive_summary, sec2_scope,
    sec3_technical_findings, sec4_lifecycle,
    sec5_conclusion, appendix1, appendix2,
)

from minio import Minio
from app.services.minio import minio_service
from app.core.config import settings

ANCHORS = {
    "sec1": "§ANCHOR§SEC1§",
    "sec2": "§ANCHOR§SEC2§",
    "sec3": "§ANCHOR§SEC3§",
    "sec4": "§ANCHOR§SEC4§",
    "sec5": "§ANCHOR§SEC5§",
    "app1": "§ANCHOR§APP1§",
    "app2": "§ANCHOR§APP2§",
}

_executor = ThreadPoolExecutor(max_workers=4)

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
        self.context.critical_cnt = sc.get("CRITICAL", 0)
        self.context.high_cnt     = sc.get("HIGH", 0)
        self.context.medium_cnt   = sc.get("MEDIUM", 0)
        self.context.low_cnt      = sc.get("LOW", 0)

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
    
    def _playwright_render(self, html: str, base_dir: str, output_path: str, browser):
        print(base_dir)
        tmp_html = base_dir / "_tmp_render.html"
        with open(tmp_html, "w", encoding="utf-8") as f:
            f.write(html)

        page = browser.new_page()
        page.goto(f"file:///{tmp_html.as_posix()}")
        page.wait_for_load_state("networkidle")
        page.pdf(
            path    = output_path,
            format  = "A4",
            margin  = {"top": "10mm","bottom": "22mm", "left": "20mm", "right": "20mm"},
            print_background      = True,
            display_header_footer = True,
            header_template = (
                "<div style=\"width:80%; font-family:sans-serif;"
                "margin: 8px 10mm 8px 10mm; border-bottom: 0.5px solid #EEEEEE\">"
                f"<div style=\"font-size:12px; font-weight:700; color:#AAAAAA; margin-bottom: 2mm\">รายงานผลการทดสอบเจาะระบบ {self.context.project_name}</div>"
                f"<div style=\"font-size:10px; font-weight:300; color:#DDDDDD; margin-bottom: 4mm\">หมายเลขเอกสาร: {self.context.report_no}</div>"
                "</div>"
            ),
            footer_template = """
                <div style="width:100%; font-family:sans-serif; font-size:8px;
                            color:#aaa; text-align:center;">
                — <span class="pageNumber"></span> —
                </div>""",
        )
        page.close()

        tmp_html.unlink()

    def _render_pdf_sync(self):
        base_dir    = Path(__file__).resolve().parent.parent.parent.parent.parent
        pass1_path  = base_dir / "fake_file_storage" / "report" / f"{self.context.report_id}" / "_pass1.pdf"
        output_path = base_dir / "fake_file_storage" / "report" / f"{self.context.report_id}" / f"{self.context.report_name}.pdf"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with sync_playwright() as p:
            browser = p.chromium.launch()

            # ── Pass 1: gen PDF พร้อม anchor markers, TOC ยังไม่มีเลขหน้า ──
            print("📄 Pass 1: generating PDF with anchor markers...")
            html, base_dir = self._build_html(page_nums={}, include_anchors=True)
            self._playwright_render(html, base_dir, pass1_path, browser)

            # ── อ่านเลขหน้าจาก PDF จริง ──
            print("🔍 Reading page numbers from PDF...")
            page_nums = self._read_page_numbers_from_pdf(pass1_path)
            print(f"   found: {page_nums}")
            pass1_path.unlink()

            # ── Pass 2: gen PDF อีกรอบพร้อมเลขหน้าใน TOC ──
            print("📄 Pass 2: generating final PDF with TOC page numbers...")
            html, base_dir = self._build_html(page_nums=page_nums, include_anchors=False)
            self._playwright_render(html, base_dir, output_path, browser)

            browser.close()

            # Upload the generated PDF to MinIO
            minio_service.upload_file(
                bucket_name=settings.MINIO_REPORT_BUCKET,
                object_name=f"{self.context.report_id}/{self.context.report_name}.pdf",
                file_path=output_path,
                content_type="application/pdf"
            )


        print(f"✅ PDF saved → {output_path}")

    def gen_report_sync(self) -> tuple[Path, Path]:
        """Full sync report generation — PDF + DOCX."""
        self._render_pdf_sync()

        base_dir  = Path(__file__).resolve().parent.parent.parent.parent.parent
        pdf_path  = base_dir / "fake_file_storage" / "report" / f"{self.context.report_id}" / f"{self.context.report_name}.pdf"
        docx_path = base_dir / "fake_file_storage" / "report" / f"{self.context.report_id}" / f"{self.context.report_name}.docx"

        cv = Converter(str(pdf_path))
        cv.convert(str(docx_path))
        cv.close()

        # Upload the generated DOCX to MinIO
        minio_service.upload_file(
            bucket_name=settings.MINIO_REPORT_BUCKET,
            object_name=f"{self.context.report_id}/{self.context.report_name}.docx",
            file_path=docx_path,
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

        print(f"✅ DOCX saved → {docx_path}")
        
        pdf_path.unlink()
        docx_path.unlink()

        pdf_path = f"{self.context.report_id}/{self.context.report_name}.pdf"
        docx_path = f"{self.context.report_id}/{self.context.report_name}.docx"

        return pdf_path, docx_path


    async def gen_report(self) -> tuple[Path, Path]:
        """✅ ป้องกันการยกเลิก Task แม้ Request จะหลุดไปก่อน"""
        loop = asyncio.get_event_loop()
        
        # ใช้ shield เพื่อบอกว่าห้ามยกเลิกงานนี้
        # และใช้ try-except เพื่อจัดการ Log กรณีเกิดปัญหา
        try:
            # สร้าง Coroutine สำหรับรันงานใน Executor
            task = loop.run_in_executor(_executor, self.gen_report_sync)
            return await asyncio.shield(task)
        except asyncio.CancelledError:
            # ถ้าโดน Cancel จริงๆ (เช่น Server Shutdown) ให้ Log ไว้
            print("📢 Report generation was shielded but still cancelled by system shutdown.")
            raise
