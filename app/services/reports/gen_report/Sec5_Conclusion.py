from reportlab.platypus import ListFlowable, ListItem, Paragraph, Spacer

def create_conclusion(context, styles):

    elements = []

    # ==========================
    # 5. Conclusion
    # ==========================

    elements.append(
        Paragraph(
            "<font name='Sarabun-SemiBold'>5. บทสรุปและข้อเสนอแนะ (Conclusion and Recommendations)</font>",
            styles["section"]
        )
    )
    elements.append(Spacer(1, 12))

    # ==========================
    # 5.1 Overall Security Conclusion
    # ==========================

    elements.append(
        Paragraph(
            "<font name='Sarabun-SemiBold'>5.1. บทสรุปภาพรวมความปลอดภัย (Overall Security Conclusion)</font>",
            styles["section"]
        )
    )
    elements.append(Spacer(1, 6))

    format_text = f"จากการทดสอบเจาะระบบภายใต้โครงการ {context.project_name} โดยใช้ระบบตรวจสอบอัตโนมัติ {context.scanner_name} ผลการประเมินชี้ให้เห็นว่าสภาวะความมั่นคงปลอดภัยของระบบอยู่ในระดับ [วิกฤต/สูง/ปานกลาง] แม้ระบบจะมีการป้องกันในระดับโครงสร้างพื้นฐานเบื้องต้น แต่ยังคงตรวจพบช่องโหว่ทางเทคนิคที่สำคัญในส่วนของ [ระบุส่วนที่พบช่องโหว่ เช่น ระบบบริหารจัดการข้อมูล หรือ API Service] ซึ่งหากไม่ได้รับการแก้ไขอย่างทันท่วงที อาจส่งผลกระทบต่อความลับ (Confidentiality) และความถูกต้องสมบูรณ์ (Integrity) ของข้อมูลในระดับองค์กร"
    elements.append(Paragraph(format_text, styles["body"]))
    elements.append(Spacer(1, 12))

    # ==========================
    # 5.2 Efficiency
    # ==========================

    elements.append(
        Paragraph(
            "<font name='Sarabun-SemiBold'>5.2. การประเมินประสิทธิภาพของระบบ Security Worker</font>",
            styles["section"]
        )
    )
    elements.append(Spacer(1, 6))

    bridge_text = f"การนำระบบอัตโนมัติมาใช้ในโครงการนี้ ช่วยให้กระบวนการตรวจสอบมีประสิทธิภาพเพิ่มขึ้นในมิติต่างๆ ดังนี้:"
    elements.append(Paragraph(bridge_text, styles["body"]))
    elements.append(Spacer(1, 10))

    efficiency_points = [
        f"Deep Visibility: สามารถตรวจพบช่องโหว่ในส่วนของ API Endpoints ที่ไม่มีการระบุไว้ในเอกสาร (Shadow API) ผ่านการทำ Traffic Interception ในขณะสแกน",
        f"Accuracy & Reliability: เทคนิค Dynamic Verification ช่วยลดอัตราการเกิดผลการตรวจผิดพลาด (False Positive) ได้อย่างมีนัยสำคัญ ทำให้ทีมพัฒนาได้รับข้อมูลที่แม่นยำเพื่อการแก้ไขที่ตรงจุด",
        f"Documentation Speed: ระบบสามารถจัดทำหลักฐานการยืนยัน (PoC) ทั้งในรูปแบบภาพหน้าจอและคำสั่ง cURL ได้ทันทีหลังจากตรวจพบช่องโหว่ ช่วยลดระยะเวลาในการทำรายงานได้ถึง {context.efficiency}%"
    ]

    elements.append(
        ListFlowable(
            [ListItem(Paragraph(point, styles["body"])) for point in efficiency_points],
            bulletType="bullet"
        )
    )
    elements.append(Spacer(1, 12))

    # ==========================
    # 5.3 Strategic Recommendations
    # ==========================

    elements.append(
        Paragraph(
            "<font name='Sarabun-SemiBold'>5.3. ข้อเสนอแนะเพื่อการปรับปรุง (Strategic Recommendations)</font>",
            styles["section"]
        )
    )
    elements.append(Spacer(1, 6))

    recommendations = [
        f"Remediation Priority: ควรเร่งดำเนินการแก้ไขช่องโหว่ระดับ Critical และ High ทั้งหมด และดำเนินการทดสอบซ้ำ (Re-testing) เพื่อปิดวงจรการจัดการความเสี่ยง",
        f"Integration with DevSecOps: แนะนำให้บูรณาการระบบ Security Worker เข้าเป็นส่วนหนึ่งของขั้นตอนการพัฒนาซอฟต์แวร์ (CI/CD Pipeline) เพื่อสร้างกลไกการตรวจสอบความปลอดภัยอย่างต่อเนื่อง",
        f"Security Training: ควรส่งเสริมความรู้ด้านการเขียนโปรแกรมอย่างปลอดภัย (Secure Coding) ให้แก่ทีมงานตามมาตรฐาน OWASP เพื่อลดการเกิดช่องโหว่ซ้ำในอนาคต"
    ]

    elements.append(
        ListFlowable(
            [ListItem(Paragraph(point, styles["body"])) for point in recommendations],
            bulletType="bullet"
        )
    )
    elements.append(Spacer(1, 12))

    return elements