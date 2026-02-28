from reportlab.platypus import Paragraph, Spacer
from reportlab.lib.units import inch

def create_cover_page(context, styles):

    elements = []

    title = "รายงานผลการทดสอบเจาะระบบ (Penetration Testing Report)<br/><br/>"
    projectBold = "โครงการ (Project): "
    project = f"{context.project_name}<br/>"
    jobBold = "หมายเลขเอกสาร (Job ID): "
    job = f"{context.job_id}<br/>"
    dateBold = "วันที่ทดสอบ: "
    date = f"{context.job_started_date} – {context.job_ended_date}<br/>"
    scannerBold = "จัดเตรียมโดย: "
    scanner = f"{context.scanner_name}<br/>"
    supportEmailBold = "อีเมลสนับสนุน: "
    supportEmail = f"{context.support_email}"

    elements.append(Paragraph(title, styles["title"]))
    elements.append(
        Paragraph(
            f'<font name="Sarabun-Bold">{projectBold}</font> '
            f'<font name="Sarabun-Regular">{project}</font>',
            styles["body_cover"]
        )
    )
    elements.append(Spacer(1, 0.2 * inch))
    elements.append(
        Paragraph(
            f'<font name="Sarabun-Bold">{jobBold}</font> '
            f'<font name="Sarabun-Regular">{job}</font>',
            styles["body_cover"]
        )
    )
    elements.append(Spacer(1, 0.2 * inch))
    elements.append(
        Paragraph(
            f'<font name="Sarabun-Bold">{dateBold}</font> '
            f'<font name="Sarabun-Regular">{date}</font>',
            styles["body_cover"]
        )
    )
    elements.append(Spacer(1, 0.2 * inch))
    elements.append(
        Paragraph(
            f'<font name="Sarabun-Bold">{scannerBold}</font> '
            f'<font name="Sarabun-Regular">{scanner}</font>',
            styles["body_cover"]
        )
    )
    elements.append(Spacer(1, 0.2 * inch))
    elements.append(
        Paragraph(
            f'<font name="Sarabun-Bold">{supportEmailBold}</font> '
            f'<font name="Sarabun-Regular">{supportEmail}</font>',
            styles["body_cover"]
        )
    )

    return elements
