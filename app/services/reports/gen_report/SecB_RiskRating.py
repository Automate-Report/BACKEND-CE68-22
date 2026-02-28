from reportlab.platypus import ListFlowable, ListItem, PageBreak, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

def create_risk_rating(context, styles):

    elements = []

    # ==========================
    # Appendix 2: Risk Rating
    # ==========================

    elements.append(
        Paragraph(
            "<font name='Sarabun-SemiBold'>ภาคผนวก 2: เกณฑ์การประเมินระดับความเสี่ยง (Risk Rating)</font>",
            styles["section"]
        )
    )
    elements.append(Spacer(1, 12))

    elements.append(
        Paragraph(
            "การประเมินความเสี่ยงของช่องโหว่สารสนเทศในโครงการนี้ "
            "อ้างอิงตามมาตรฐานสากล 2 รูปแบบ เพื่อให้ครอบคลุมทั้งมิติความเป็นไปได้ในการโจมตี "
            "และผลกระทบที่อาจเกิดขึ้นจริง",
            styles["body"]
        )
    )
    elements.append(Spacer(1, 16))


    # ==========================
    # 1. OWASP Risk Rating
    # ==========================

    elements.append(
        Paragraph(
            "<font name='Sarabun-SemiBold'>1. วิธีการประเมินความเสี่ยงตามมาตรฐาน OWASP (OWASP Risk Rating)</font>",
            styles["body"]
        )
    )
    elements.append(Spacer(1, 10))

    elements.append(
        Paragraph(
            "การคำนวณระดับความเสี่ยง (Risk) อ้างอิงตามความสัมพันธ์ระหว่าง "
            "ความเป็นไปได้ที่จะถูกโจมตี (Likelihood) และผลกระทบที่จะได้รับ (Impact) ตามสูตร:",
            styles["body"]
        )
    )
    elements.append(Spacer(1, 10))

    elements.append(
        Paragraph(
            "<font name='Sarabun-SemiBold'>"
            "ความเสี่ยง (Risk) = ความเป็นไปได้ (Likelihood) × ผลกระทบ (Impact)"
            "</font>",
            styles["center"]
        )
    )
    elements.append(Spacer(1, 16))


    # ==========================
    # 1.1 ตัวแปรที่ใช้ในการคำนวณ
    # ==========================

    elements.append(
        Paragraph(
            "<font name='Sarabun-SemiBold'>1.1 ตัวแปรที่ใช้ในการคำนวณ</font>",
            styles["body"]
        )
    )
    elements.append(Spacer(1, 8))

    elements.append(
        Paragraph(
            "ระบบทำการประเมินโดยให้คะแนนตัวแปรแต่ละด้านตั้งแต่ 0 ถึง 9 ดังนี้:",
            styles["body"]
        )
    )
    elements.append(Spacer(1, 10))


    # Likelihood Factors
    elements.append(
        Paragraph(
            "<font name='Sarabun-SemiBold'>ก. ปัจจัยด้านความเป็นไปได้ (Likelihood Factors):</font>",
            styles["body"]
        )
    )
    elements.append(Spacer(1, 6))

    likelihood_points = [
        "<font name='Sarabun-SemiBold'>Threat Agent Factors:</font> "
        "ประเมินจากความสามารถของผู้โจมตี (Skill Level), "
        "แรงจูงใจ (Motive) และจำนวนกลุ่มผู้โจมตี (Size)",

        "<font name='Sarabun-SemiBold'>Vulnerability Factors:</font> "
        "ประเมินจากความยากง่ายในการค้นพบ (Ease of discovery), "
        "ความยากง่ายในการโจมตี (Ease of exploit), "
        "ความรู้ต่อช่องโหว่ (Awareness) และ "
        "ความสามารถของระบบตรวจจับ (Intrusion detection)"
    ]

    elements.append(
        ListFlowable(
            [ListItem(Paragraph(point, styles["body"])) for point in likelihood_points],
            bulletType="bullet"
        )
    )
    elements.append(Spacer(1, 12))



    # Impact Factors
    elements.append(
        Paragraph(
            "<font name='Sarabun-SemiBold'>ข. ปัจจัยด้านผลกระทบ (Impact Factors):</font>",
            styles["body"]
        )
    )
    elements.append(Spacer(1, 6))

    impact_points = [
        "<font name='Sarabun-SemiBold'>Technical Impact:</font> "
        "ประเมินผลกระทบต่อความลับของข้อมูล (Confidentiality), "
        "ความถูกต้อง (Integrity), ความพร้อมใช้งาน (Availability) "
        "และความรับผิดชอบ (Accountability)",

        "<font name='Sarabun-SemiBold'>Business Impact:</font> "
        "ประเมินความเสียหายด้านการเงิน (Financial), ชื่อเสียง (Reputation), "
        "ข้อกฎหมาย (Compliance) และความเป็นส่วนตัว (Privacy)"
    ]

    elements.append(
        ListFlowable(
            [ListItem(Paragraph(point, styles["body"])) for point in impact_points],
            bulletType="bullet"
        )
    )
    elements.append(Spacer(1, 12))

    # ==========================
    # 1.2 Overall Risk Level
    # ==========================

    elements.append(
        Paragraph(
            "<font name='Sarabun-SemiBold'>1.2 การกำหนดระดับความเสี่ยงโดยรวม (Overall Risk Level)</font>",
            styles["body"]
        )
    )
    elements.append(Spacer(1, 10))

    elements.append(
        Paragraph(
            "หลังจากคำนวณคะแนนความเสี่ยงแล้ว ระบบจะทำการแปลงคะแนนดังกล่าวให้อยู่ในรูปแบบระดับ ความรุนแรงเชิงคุณภาพ (Qualitative Risk Level) เพื่อใช้ในการสื่อสารเชิงบริหารและจัดลำดับ ความสำคัญในการแก้ไขช่องโหว่",
            styles["body"]
        )
    )
    elements.append(Spacer(1, 12))
    elements.append(PageBreak())

    # ==========================
    # Risk Level Mapping Table
    # ==========================

    table_data = [
        ["คะแนนความเสี่ยงของช่องโหว่","ระดับความเสี่ยงของช่องโหว่"],
        ["ตั้งแต่ 0 ถึง 3", "ต่ำ"],
        ["ตั้งแต่ 3 ถึง 6", "ปานกลาง"],
        ["ตั้งแต่ 6 ถึง 9", "สูง"],
    ]

    risk_table = Table(table_data, colWidths=[220, 150], repeatRows=1)

    risk_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, -1), "Sarabun-Regular"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    elements.append(risk_table)
    elements.append(Spacer(1, 20))

    # ==========================
    # 2.	วิธีการประเมินความเสี่ยงตามมาตรฐาน CVSS v3.1
    # ==========================

    elements.append(
        Paragraph(
            "<font name='Sarabun-SemiBold'>2. วิธีการประเมินความเสี่ยงตามมาตรฐาน CVSS v3.1</font>",
            styles["body"]
        )
    )
    elements.append(Spacer(1, 10))

    text = f"ระบบ {context.scanner_name} ยึดถือคะแนน CVSS v3.1 (Common Vulnerability Scoring System) เป็นเกณฑ์หลักในการรายงานผล เนื่องจากเป็นมาตรฐานสากลที่ได้รับยอมรับโดย NIST โดยพิจารณาจากกลุ่มตัวแปรพื้นฐาน (Base Metric Group):"
    elements.append(Paragraph(text, styles["body"]))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("ตารางสรุปเกณฑ์คะแนนและระดับความรุนแรง (CVSS v3.1 Rating)", styles["body"]))
    elements.append(Spacer(1, 12))

    # ==========================
    # Risk Level Mapping Table (2)
    # ==========================

    table_data = [
        ["คะแนนความเสี่ยงของช่องโหว่","ระดับความเสี่ยงของช่องโหว่"],
        ["0", "ไม่มีความเสี่ยง"],
        ["0.1-3.9", "ต่ำ"],
        ["4.0-6.9", "ปานกลาง"],
        ["7.0-8.9", "สูง"],
        ["9.0-10.0", "สูงมาก"],
    ]

    risk_table = Table(table_data, colWidths=[220, 150], repeatRows=1)

    risk_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, -1), "Sarabun-Regular"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    elements.append(risk_table)
    elements.append(Spacer(1, 16))

    return elements