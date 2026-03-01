from reportlab.platypus import Paragraph, Spacer, PageBreak
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.styles import ParagraphStyle

def create_content_page(context, styles):

    content = []

    content.append(Paragraph("สารบัญ", styles['title_center']))
    content.append(Spacer(1, 20))

    toc = TableOfContents()

    toc.levelStyles = [

        # Level 0 (Main section)
        ParagraphStyle(
            name='TOCLevel0',
            parent=styles['bold'],
            fontSize=12,
            leftIndent=20,
            firstLineIndent=-20,
            spaceBefore=5,
            leading=14,
        ),

        # Level 1 (Subsection)
        ParagraphStyle(
            name='TOCLevel1',
            parent=styles['body'],
            fontSize=10,
            leftIndent=40,      # ← indent
            firstLineIndent=-20,
            spaceBefore=2,
            leading=12,
        ),
    ]

    content.append(toc)
    content.append(PageBreak())

    return content