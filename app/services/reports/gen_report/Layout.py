from reportlab.lib.units import mm

def draw_header(canvas, doc, context):
    canvas.saveState()

    canvas.setFont("Sarabun-Bold", 12)
    canvas.drawString(10 * mm, 285 * mm, f"รายงานผลการทดสอบเจาะระบบ {context.asset_name}")

    canvas.setFont("Sarabun-Regular", 10)
    canvas.drawString(10 * mm, 278 * mm, f"หมายเลขเอกสาร: {context.job_name}")

    canvas.restoreState()


def draw_footer(canvas, doc):
    canvas.saveState()

    canvas.setFont("Sarabun-Regular", 9)
    page_number_text = f"Page {doc.page}"
    canvas.drawCentredString(105 * mm, 10 * mm, page_number_text)

    canvas.restoreState()


def draw_page(context, canvas, doc):
    draw_header(canvas, doc, context)
    draw_footer(canvas, doc)