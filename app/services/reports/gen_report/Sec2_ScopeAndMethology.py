from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
from reportlab.platypus import ListFlowable, ListItem
from reportlab.lib import colors


def create_scope_and_methology(context, styles):

    elements = []

    # ==========================
    # 2. Scope and Methodology
    # ==========================

    elements.append(
        Paragraph("2. ขอบเขตและระเบียบวิธีการปฏิบัติงาน (Scope and Methodology)", styles["section"])
    )
    elements.append(Spacer(1, 12))

    # ==========================
    # 2.1 Audit Scope
    # ==========================

    elements.append(
        Paragraph("2.1. ขอบเขตของสินทรัพย์ที่ทำการตรวจสอบ (Audit Scope)", styles["section"])
    )
    elements.append(Spacer(1, 6))

    bridge_text = f"มีรายละเอียดสินทรัพย์ ดังนี้"
    elements.append(Paragraph(bridge_text, styles["body"]))
    elements.append(Spacer(1, 10))

    # Table header
    table_data = [
        [
            "ลำดับที่",
            "ชื่อระบบ\n(Asset Name)",
            "รายละเอียดและขอบเขตบริการ",
            "หมายเลขไอพี / \nโดเมนเป้าหมาย"
        ]
    ]

    # Add rows
    asset_cnt = 1
    for asset in context.assets:
        table_data.append([
            asset_cnt,
            asset["asset_name"],
            asset["asset_desc"],
            asset["target"],
        ])
        asset_cnt += 1

    table = Table(table_data, repeatRows=1)

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, -1), "Sarabun-Regular"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 16))

    # ==========================
    # 2.2 Technical Architecture
    # ==========================
    elements.append(
        Paragraph("2.2. สถาปัตยกรรมการทดสอบและเทคโนโลยีที่ใช้ (Technical Architecture)", styles["section"])
    )
    elements.append(Spacer(1, 6))

    bridge_text = f"การทดสอบดำเนินการผ่านระบบสแกนอัตโนมัติ (Automated Security Engine) ซึ่งมีจุดเด่นในด้าน การทำงานแบบกระจายศูนย์ (Distributed Architecture) โดยมีขั้นตอนการดำเนินงานเชิงเทคนิค ดังนี้"
    elements.append(Paragraph(bridge_text, styles["body"]))
    elements.append(Spacer(1, 10))

    # Numbered list
    steps = [
        f"<font name='Sarabun-Semibold'>Asset Configuration</font>: ผู้ใช้งาน (User) ดำเนินการระบุเป้าหมายและขอบเขตการทดสอบผ่าน แพลตฟอร์มบริหารจัดการส่วนกลาง (Centralized Management Website) เพื่อกำหนดโครงสร้างพารามิเตอร์และสิทธิ์การเข้าถึง (Authentication)",
        f"<font name='Sarabun-Semibold'>Worker Deployment</font>: ผู้ใช้งานทำการติดตั้งส่วนประกอบตรวจสอบ (Security Worker) ลงในเครื่องคอมพิวเตอร์ที่ใช้สำหรับการทดสอบ (Dedicated Pentest Machine) โดยตัว Worker จะทำหน้าที่เป็นตัวแทนในการดำเนินการโจมตีเชิงรุกตามคำสั่งที่ได้รับมอบหมาย",
        f"<font name='Sarabun-Semibold'>Autonomous Execution</font>: เมื่อระบบเริ่มทำงาน Security Worker จะดำเนินการสแกนแบบอัตโนมัติโดยสมบูรณ์ (Fully Automated Scanning) ครอบคลุมตั้งแต่การขุดหาเส้นทาง API (Endpoint Discovery) ไปจนถึงการวิเคราะห์ช่องโหว่เชิงลึก"
    ]

    elements.append(
        ListFlowable(
            [ListItem(Paragraph(item, styles["body"])) for item in steps],
            bulletType="bullet"
        )
    )
    elements.append(Spacer(1, 16))

    # ==========================
    # 2.3 Automated Testing Process
    # ==========================
    elements.append(
        Paragraph("2.3. ขั้นตอนการทดสอบด้วยระบบอัตโนมัติ (Automated Testing Process)", styles["section"])
    )
    elements.append(Spacer(1, 6))

    bridge_text = f"""ระบบ Worker ดำเนินการทดสอบโดยอ้างอิงตามมาตรฐานความปลอดภัยสากล ผ่านกลไกการทำงาน ดังนี้"""
    elements.append(Paragraph(bridge_text, styles["body"]))
    elements.append(Spacer(1, 10))

    # Bullet list
    process_steps = [
        f"<font name='Sarabun-Semibold'>Stateful Discovery</font>: ใช้เทคโนโลยี Browser Automation (Playwright) เพื่อจำลองการทำงานของผู้ใช้จริง สามารถจัดการ Session (Cookies/LocalStorage) และข้ามผ่านระบบยืนยันตัวตนเพื่อเข้าถึงหน้าเว็บ ที่อยู่หลังระบบล็อกอินได้โดยอัตโนมัติ",
        f"<font name='Sarabun-Semibold'>Dynamic Traffic Interception</font>: ทำการดักจับและวิเคราะห์ Network Traffic (XHR/Fetch) ในระดับ Runtime เพื่อค้นหาพารามิเตอร์และ API Endpoints ที่ซ่อนอยู่ ซึ่งเครื่องมือสแกนทั่วไปมักตรวจไม่พบ",
        f"<font name='Sarabun-Semibold'>Intelligent Payload Injection</font>: วิเคราะห์บริบทของตัวแปร (Context Analysis) เพื่อเลือกชุดคำสั่งโจมตี (Payloads) ที่เหมาะสมกับสถาปัตยกรรมของเป้าหมาย ลดการเกิด Noise ในระบบและเพิ่มความแม่นยำ ในการตรวจพบ",
        f"<font name='Sarabun-Semibold'>Proof of Concept (PoC) Generation</font>: เมื่อตรวจพบช่องโหว่ ระบบจะทำการบันทึกหลักฐานในรูปแบบภาพหน้าจอ (Visual Evidence) และคำสั่งจำลองการโจมตี (cURL Command) เพื่อใช้สำหรับการยืนยันและแก้ไขในลำดับถัดไป"
    ]

    elements.append(
        ListFlowable(
            [ListItem(Paragraph(item, styles["body"])) for item in process_steps],
            bulletType="bullet"
        )
    )

    elements.append(Spacer(1, 16))

    return elements