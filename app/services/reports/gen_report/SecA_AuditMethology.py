from reportlab.platypus import ListFlowable, ListItem, PageBreak, Paragraph, Spacer

def create_audit_methology(context, styles):

    elements = []

    # ==========================
    # Audit Methodology
    # ==========================
    elements.append(
        Paragraph(
            "<font name='Sarabun-SemiBold'>ภาคผนวก 1: รายละเอียดวิธีการและขั้นตอนการตรวจประเมิน (Audit Methodology)</font>",
            styles["section"]
        )
    )
    elements.append(Spacer(1, 12))

    format_text = f"วิธีการตรวจประเมินและกระบวนการทดสอบอ้างอิงตามมาตรฐานสากล OWASP Top 10:2021 และ NIST SP 800-115 โดยมีการประยุกต์ใช้เทคโนโลยี Security Worker ในรูปแบบการทำงาน 4 ขั้นตอนหลัก ดังนี้"
    elements.append(Paragraph(format_text, styles["body"]))
    elements.append(Spacer(1, 10))

    # ==========================
    # Information Gathering
    # ==========================
    elements.append(
        Paragraph(
            "<font name='Sarabun-SemiBold'>1. การรวบรวมข้อมูล (Information Gathering)</font>",
            styles["section"]
        )
    )
    elements.append(Spacer(1, 10))

    info_gathering_points = [
        f"Active Reconnaissance: ระบบดำเนินการสำรวจโครงสร้างของเว็บแอปพลิเคชันโดยอัตโนมัติผ่านตัวควบคุมเบราว์เซอร์ (Browser Automation)",
        f"Network Traffic Interception: ใช้เทคโนโลยี Playwright Interception ดักจับข้อมูลการสื่อสารระหว่าง Client และ Server (XHR/Fetch) เพื่อค้นหา API Endpoint และวิเคราะห์การจัดการ Session ผ่าน Cookies หรือ LocalStorage",
        f"DNS & Service Discovery: ตรวจสอบข้อมูล DNS และค่าหมายเลขไอพีเพื่อกำหนดขอบเขตของการทดสอบ (Scoping) ให้มีความชัดเจน"
    ]
    elements.append(
        ListFlowable(
            [ListItem(Paragraph(point, styles["body"])) for point in info_gathering_points],
            bulletType="bullet"
        )
    )
    elements.append(Spacer(1, 12))

    # ==========================
    # Vulnerability Identification
    # ==========================
    elements.append(
        Paragraph(
            "<font name='Sarabun-SemiBold'>2. การระบุและวิเคราะห์ช่องโหว่ (Vulnerability Identification)</font>",
            styles["section"]
        )
    )
    elements.append(Spacer(1, 10))

    vuln_identification_points = [
        f"Monkey Patching Technology: สอดแทรกคำสั่งตรวจสอบ (Probes) เข้าไปในกระบวนการทำงานของเบราว์เซอร์แบบ Runtime เพื่อวิเคราะห์พฤติกรรมการประมวลผลโค้ดในเชิงลึก",
        f"Context-Aware Fuzzing: วิเคราะห์บริบทของพารามิเตอร์แต่ละตัวเพื่อส่งชุดข้อมูลทดสอบ (Probe Strings) ที่เหมาะสมกับสถาปัตยกรรมของแอปพลิเคชันนั้นๆ",
        f"Vulnerability Library Matching: เปรียบเทียบผลลัพธ์ที่ได้กับคลังข้อมูลช่องโหว่มาตรฐาน (เช่น SQLi, XSS, Path Traversal) เพื่อระบุประเภทความเสี่ยง"
    ]

    elements.append(
        ListFlowable(
            [ListItem(Paragraph(point, styles["body"])) for point in vuln_identification_points],
            bulletType="bullet"
        )
    )
    elements.append(Spacer(1, 12))

    # ==========================
    # Exploitation & Verification
    # ==========================
    elements.append(
        Paragraph(
            "<font name='Sarabun-SemiBold'>3. การทดสอบการบุกรุกเพื่อยืนยันผล (Exploitation & Verification)</font>",
            styles["section"]
        )
    )
    elements.append(Spacer(1, 10))

    exploitation_points = [
        f"Dynamic Payload Injection: ดำเนินการส่งชุดคำสั่งโจมตี (Payloads) ที่ออกแบบมาเพื่อการตรวจสอบ (Non-destructive) เพื่อยืนยันว่าช่องโหว่นั้นสามารถโจมตีได้จริง",
        f"Automated Confirmation Signal: ระบบจะรอรับสัญญาณการตอบสนองที่ระบุไว้ในเงื่อนไข (เช่น สัญญาณ XSS_CONFIRMED) เพื่อยืนยันความถูกต้องของผลลัพธ์และป้องกันการรายงานผลผิดพลาด",
        f"Access Control Testing: ทดสอบการเข้าถึงฟังก์ชันสำคัญโดยใช้สิทธิ์ที่จำกัด เพื่อประเมินความเป็นไปได้ในการยกระดับสิทธิ์ (Privilege Escalation)"
    ]

    elements.append(
        ListFlowable(
            [ListItem(Paragraph(point, styles["body"])) for point in exploitation_points],
            bulletType="bullet"
        )
    )
    elements.append(Spacer(1, 12))
    elements.append(PageBreak())

    # ==========================
    # Analysis & Documentation
    # ==========================
    elements.append(
        Paragraph(
            "<font name='Sarabun-SemiBold'>4. การวิเคราะห์ผลและจัดทำรายงาน (Analysis & Documentation)</font>",
            styles["section"]
        )
    )
    elements.append(Spacer(1, 10))

    analysis_points = [
        f"Evidence Collection: ระบบทำการบันทึกหลักฐานเชิงประจักษ์โดยอัตโนมัติ รวมถึงภาพถ่ายหน้าจอที่ระบุจุดผิดปกติ และคำสั่ง cURL ที่ใช้ในการจำลองการโจมตี",
        f"Vulnerability Lifecycle Mapping: นำข้อมูลที่พบเข้าสู่ระบบการบริหารจัดการ เพื่อมอบหมาย (Assign) ให้กับผู้รับผิดชอบ และเตรียมความพร้อมสำหรับการทดสอบซ้ำ (Re-test) ในลำดับถัดไป"
    ]

    elements.append(
        ListFlowable(
            [ListItem(Paragraph(point, styles["body"])) for point in analysis_points],
            bulletType="bullet"
        )
    )
    elements.append(Spacer(1, 12))

    return elements