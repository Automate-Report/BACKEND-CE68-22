from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
from reportlab.platypus import ListFlowable, ListItem
from reportlab.lib import colors


def create_executive_summary(context, styles):

    elements = []

    # ==========================
    # 1. Executive Summary
    # ==========================

    elements.append(
        Paragraph("1. บทสรุปผู้บริหาร (Executive Summary)", styles["section"])
    )
    elements.append(Spacer(1, 12))

    # ==========================
    # 1.1 Objective
    # ==========================

    elements.append(
        Paragraph("1.1 วัตถุประสงค์และภาพรวมการดำเนินงาน (Project Objective & Overview)", styles["section"])
    )
    elements.append(Spacer(1, 6))

    objective_text = f"การทดสอบเจาะระบบ (Penetration Testing) สำหรับโครงการ {context.project_name} มีวัตถุประสงค์เพื่อประเมินระดับความมั่นคงปลอดภัยและค้นหาช่องโหว่ที่อาจส่งผลกระทบต่อการดำเนินธุรกิจโดยอาศัยเทคนิคการตรวจสอบเชิงลึกจากระบบเครือข่ายและแอปพลิเคชันในรูปแบบ Gray Box Testing"
    elements.append(Paragraph(objective_text, styles["body"]))
    elements.append(Spacer(1, 12))

    # ==========================
    # 1.2 Vulnerability Profile
    # ==========================

    elements.append(
        Paragraph("1.2 สรุปสถานะความเสี่ยงตามระดับความรุนแรง (Vulnerability Profile)", styles["section"])
    )
    elements.append(Spacer(1, 6))

    summary_text = f"จากการประเมินเชิงเทคนิค ระบบตรวจพบช่องโหว่จำนวนรวมทั้งสิ้น {context.total_vulns} รายการจากจำนวนสินทรัพย์ (Asset) ทั้งหมด {context.total_asset} รายการโดยสามารถจัดกลุ่มตามระดับความรุนแรงตาม CVSS v3.1 ได้ดังนี้"
    elements.append(Paragraph(summary_text, styles["body"]))
    elements.append(Spacer(1, 10))

    # Bullet list
    vuln_list = [
        f"<font name='Sarabun-Semibold'>Critical</font> (วิกฤต): {context.critical_cnt} ข้อ",
        f"<font name='Sarabun-Semibold'>High</font> (สูง): {context.high_cnt} ข้อ",
        f"<font name='Sarabun-Semibold'>Medium</font> (กลาง): {context.medium_cnt} ข้อ",
        f"<font name='Sarabun-Semibold'>Low</font> (ต่ำ): {context.low_cnt} ข้อ",
    ]

    elements.append(
        ListFlowable(
            [ListItem(Paragraph(item, styles["body"])) for item in vuln_list],
            bulletType="bullet"
        )
    )

    elements.append(Spacer(1, 12))

    # ==========================
    # 1.3 Vulnerability Dashboard
    # ==========================

    elements.append(
        Paragraph("1.3 Vulnerability Dashboard", styles["section"])
    )
    elements.append(Spacer(1, 6))

    elements.append(
        Paragraph("(Graph will be inserted here)", styles["body_small"])
    )

    elements.append(Spacer(1, 16))

    # ==========================
    # 1.4 Asset-Based Risk Summary
    # ==========================

    elements.append(
        Paragraph("1.4 สรุปผลการประเมินรายสินทรัพย์ (Asset-Based Risk Summary)", styles["section"])
    )
    elements.append(Spacer(1, 10))

    # Table header
    table_data = [
        [
            "Asset ID",
            "ชื่อสินทรัพย์\n(Asset Name)",
            "เส้นทางเชื่อมต่อ\n(IP/URL)",
            "ช่องโหว่ความรุนแรงสูง",
            "สถานะการจัดการ\n(Status)"
        ]
    ]

    # Add asset rows
    for asset in context.assets:
        table_data.append([
            asset["asset_id"],
            asset["asset_name"],
            asset["target"],
            asset["hc_cnt"],
            asset["status"],
        ])

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
    # 1.5 Management Recommendations
    # ==========================
    elements.append(
        Paragraph("1.5 ข้อเสนอแนะการบริหารจัดการ (Management Recommendations)", styles["section"])
    )
    elements.append(Spacer(1, 10))
    reccommendation_text = f"เพื่อให้ระดับความมั่นคงปลอดภัยอยู่ในเกณฑ์มาตรฐาน องค์กรควรพิจารณาดำเนินการดังนี้:"
    elements.append(Paragraph(reccommendation_text, styles["body"]))

    # Bullet list
    rec_list = [
        f"<font name='Sarabun-Semibold'>ระยะสั้น</font>: มอบหมายผู้รับผิดชอบ (Assignee) เข้าแก้ไขช่องโหว่ระดับวิกฤตและระดับสูง พร้อมทั้งทำการทดสอบซ้ำ (Re-testing) เพื่อยืนยันผลการปิดช่องโหว่",
        f"<font name='Sarabun-Semibold'>ระยะกลาง</font>: บูรณาการระบบตรวจสอบความปลอดภัยอัตโนมัติเข้ากับวงจรการพัฒนาซอฟต์แวร์ (DevSecOps) เพื่อตรวจพบความบกพร่องตั้งแต่ระยะเริ่มต้น",
        f"<font name='Sarabun-Semibold'>ระยะยาว</font>: พัฒนาทักษะบุคลากรด้าน Security Coding และปรับปรุงนโยบายความมั่นคงปลอดภัยสารสนเทศตามมาตรฐาน ISO/IEC 27001 หรือ NIST Framework",
    ]

    elements.append(
        ListFlowable(
            [ListItem(Paragraph(item, styles["body"])) for item in rec_list],
            bulletType="bullet"
        )
    )

    return elements