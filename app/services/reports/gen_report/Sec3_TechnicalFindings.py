from reportlab.platypus import PageBreak, Paragraph, Spacer, ListFlowable, ListItem, Image
from reportlab.lib.units import inch

def create_technical_findings(context, styles):

    elements = []

    # ==========================
    # 3. Technical Findings
    # ==========================
    elements.append(
        Paragraph("3. รายละเอียดผลการทดสอบทางเทคนิค (Technical Findings)", styles["section"])
    )
    elements.append(Spacer(1, 12))

    # ==========================
    # 3.1 รูปแบบการนำเสนอรายงานผลการตรวจพบ
    # ==========================
    elements.append(
        Paragraph("3.1 รูปแบบการนำเสนอรายงานผลการตรวจพบ", styles["section"])
    )
    elements.append(Spacer(1, 6))
    format_text = f"ข้อมูลในส่วนนี้จะแสดงรายละเอียดเชิงลึกของแต่ละช่องโหว่ที่ระบบ <font name='Sarabun-Bold'>{context.project_name}</font> ตรวจพบ โดยโครงสร้างของรายงานถูกออกแบบมาเพื่อรองรับกระบวนการทำงานร่วมกันระหว่าง <font name='Sarabun-Bold'>ทีมทดสอบความปลอดภัย (Security Tester)</font> และ <font name='Sarabun-Bold'>ทีมพัฒนาซอฟต์แวร์ (Software Developer)</font> ซึ่งประกอบด้วย:"
    elements.append(Paragraph(format_text, styles["body"]))
    elements.append(Spacer(1, 10))

    # Bullet list
    format_list = [
        f"<font name='Sarabun-Semibold'>Technical Evidence</font>: ข้อมูล Payload, คำสั่ง cURL และภาพถ่ายหน้าจอเพื่อใช้ในการจำลองสถานการณ์โจมตีซ้ำ (Replication)",
        f"<font name='Sarabun-Semibold'>Accountability & Workflow</font>: ข้อมูลระบุตัวตนผู้รับผิดชอบการแก้ไข (Assigned To) และผู้ตรวจสอบความถูกต้อง (Verified By) เพื่อสร้างความโปร่งใสในกระบวนการ Remediation Lifecycle"
    ]

    elements.append(
        ListFlowable(
            [ListItem(Paragraph(item, styles["body"])) for item in format_list],
            bulletType="bullet"
        )
    )
    elements.append(Spacer(1, 12))

    # ==========================
    # 3.2. รายละเอียดช่องโหว่
    # ==========================
    elements.append(
        Paragraph("3.2 รายละเอียดช่องโหว่", styles["section"])
    )
    elements.append(Spacer(1, 6))

    for vuln in context.vulns:
        elements.append(Paragraph(f"<font name='Sarabun-Bold'>รายละเอียดช่องโหว่หมายเลข: </font>{vuln['vuln_id']}", styles["body"]))
        elements.append(Spacer(1, 10))

        # --- General Information ---
        elements.append(Paragraph("<font name='Sarabun-Bold'>[ ข้อมูลทั่วไปของช่องโหว่ - General Information ]</font>", styles["body"]))
        elements.append(Spacer(1, 6))
        general_info = [
            f"ประเภทช่องโหว่ (Vulnerability Type): {vuln['vuln_type']}",
            f"ระดับความรุนแรง (Severity): {vuln['severity']} | คะแนนมาตรฐาน (CVSS v3.1): {vuln['cvss_score']}",
            f"Vector String: {vuln['cvss_vector']}",
            f"สถานะปัจจุบัน (Current Status): {vuln['status']}",
        ]
        elements.append(ListFlowable([ListItem(Paragraph(item, styles["body"])) for item in general_info], bulletType="bullet"))
        elements.append(Spacer(1, 12))

        # --- Administrative Details ---
        elements.append(Paragraph("<font name='Sarabun-Bold'>[ ข้อมูลการบริหารจัดการ (Administrative Details) ]</font>", styles["body"]))
        elements.append(Spacer(1, 6))
        admin_info = [
            f"ผู้รับผิดชอบการแก้ไข (Assigned To - Developer): {vuln['dev_name']}",
            f"ผู้ตรวจสอบความถูกต้อง (Verified By - Pen Tester): {vuln['tester_name']}",
            f"สินทรัพย์ที่เกี่ยวข้อง (Related Asset): {vuln['asset_related']}",
        ]
        elements.append(ListFlowable([ListItem(Paragraph(item, styles["body"])) for item in admin_info], bulletType="bullet"))
        elements.append(Spacer(1, 12))

        # --- Technical Context ---
        elements.append(Paragraph("<font name='Sarabun-Bold'>[ ข้อมูลเชิงเทคนิค (Technical Context) ]</font>", styles["body"]))
        elements.append(Spacer(1, 6))
        technical_info = [
            f"จุดที่พบช่องโหว่ (Location): {vuln.get('method', 'GET')} {vuln['target']}",
            f"ตัวแปรที่ได้รับผลกระทบ (Parameter): {vuln['parameter']}",
            f"คำอธิบายเชิงเทคนิค (Description):<br/>{vuln['description_from_library']}",
        ]
        elements.append(ListFlowable([ListItem(Paragraph(item, styles["body"])) for item in technical_info], bulletType="bullet"))
        elements.append(Spacer(1, 12))

        # ============================================================
        # 🛡️ Proof of Concept (ปรับปรุงส่วน Payload และ Image)
        # ============================================================
        elements.append(Paragraph("<font name='Sarabun-Bold'>[ หลักฐานการยืนยันช่องโหว่ (Proof of Concept - PoC) ]</font>", styles["body"]))
        elements.append(Spacer(1, 6))

        # 1. แสดง Payload และ cURL (ใช้ Preformatted สำหรับโค้ดจะสวยกว่า)
        elements.append(Paragraph("<font name='Sarabun-Semibold'>Payload และคำสั่งจำลองการโจมตี:</font>", styles["body"]))
        elements.append(Spacer(1, 4))
        
        # กรองตัวอักษรพิเศษใน Payload และ cURL เรียบร้อยแล้วจาก Service
        elements.append(Paragraph(f"<b>Payload:</b> {vuln['payload']}", styles["body"]))
        elements.append(Paragraph(f"<b>cURL:</b> {vuln['curl_command']}", styles["body"]))
        elements.append(Spacer(1, 8))

        # 2. จัดการส่วนรูปภาพ (Evidence)
        elements.append(Paragraph("<font name='Sarabun-Semibold'>ภาพถ่ายหน้าจอหลักฐาน (Visual Evidence):</font>", styles["body"]))
        elements.append(Spacer(1, 4))

        img_reader = vuln.get("evidence") # นี่คือ ImageReader
        
        if img_reader:
            try:
                # 🚨 ตรวจสอบก่อนว่า img_reader ไม่ใช่ None และเป็น ImageReader จริง
                # ดึงขนาดภาพ
                img_w, img_h = img_reader.getSize()
                max_width = 440.0
                
                if img_w > 0:
                    scaling_factor = max_width / float(img_w)
                    draw_w = max_width
                    draw_h = img_h * scaling_factor
                    
                    # ✅ ใช้ ImageReader ส่งเข้าไปตรงๆ
                    evidence_img = Image(img_reader, width=draw_w, height=draw_h)
                    evidence_img.hAlign = 'CENTER'
                    elements.append(evidence_img)
                    elements.append(Spacer(1, 10))
                else:
                    elements.append(Paragraph("<i>(ไม่สามารถระบุขนาดของรูปภาพได้)</i>", styles["body"]))

            except Exception as e:
                # ถ้า Error ฟ้องเรื่อง Path แสดงว่า ReportLab พยายามหาไฟล์บนเครื่อง
                # ให้ลองใช้แนวทางส่งผ่าน BytesIO แทน
                elements.append(Paragraph(f"<font color='red'><i>(Error rendering image: {str(e)})</i></font>", styles["body"]))
        else:
            elements.append(Paragraph("<i>(ไม่พบภาพถ่ายหน้าจอหลักฐาน)</i>", styles["body"]))

        elements.append(Spacer(1, 12))

        # --- Recommendation ---
        elements.append(Paragraph("<font name='Sarabun-Bold'>[ คำแนะนำในการแก้ไข (Recommendation) ]</font>", styles["body"]))
        elements.append(Spacer(1, 4))
        elements.append(Paragraph(f"{vuln['reccommendation_from_library']}", styles["body"]))

        elements.append(PageBreak())

    return elements