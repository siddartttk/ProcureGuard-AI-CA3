"""Produce a printable problem statement using ReportLab."""
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

ROOT=Path(__file__).resolve().parents[1]
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='PGTitle',fontName='Helvetica-Bold',fontSize=26,leading=30,textColor=colors.HexColor('#0B2545'),spaceAfter=9))
styles.add(ParagraphStyle(name='PGHeading',fontName='Helvetica-Bold',fontSize=12,leading=16,textColor=colors.HexColor('#087F8C'),spaceBefore=10,spaceAfter=5))
styles.add(ParagraphStyle(name='PGBody',fontName='Helvetica',fontSize=10,leading=14,textColor=colors.HexColor('#243C53'),spaceAfter=7))
text=(ROOT/'docs/problem_statement.md').read_text(encoding='utf-8')
story=[]
paragraph=[]
def flush():
    if paragraph:
        clean=escape('\n'.join(paragraph).replace('**','')).replace('  \n','<br/>').replace('\n',' ')
        story.append(Paragraph(clean,styles['PGBody']))
        paragraph.clear()
for line in text.splitlines():
    if line.startswith('# '):
        flush(); story.append(Paragraph(escape(line[2:]),styles['PGTitle']))
    elif line.startswith('## '):
        flush(); story.append(Paragraph(escape(line[3:]),styles['PGHeading']))
    elif not line.strip(): flush()
    else: paragraph.append(line)
flush()

def footer(canvas,doc):
    canvas.setStrokeColor(colors.HexColor('#087F8C')); canvas.line(44,40,551,40)
    canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#243C53'))
    canvas.drawString(44,27,'ProcureGuard AI | CA-3 | AIML-C, SIT Pune | Synthetic data only')
    canvas.drawRightString(551,27,str(doc.page))

doc=SimpleDocTemplate(str(ROOT/'docs/problem_statement.pdf'),pagesize=A4,rightMargin=44,leftMargin=44,topMargin=35,bottomMargin=52,title='ProcureGuard AI - Problem Statement',author='Rishi Dwivedi and Siddarth Singh Kushwah')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print(ROOT/'docs/problem_statement.pdf')
