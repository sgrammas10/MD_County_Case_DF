import fitz
import re
from collections import defaultdict
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# --- Category definitions (from Defined Terms PDF color coding) ---
# Yellow = Circuit Court Conviction
YELLOW = {'DPGPLE','GPLD','ALGLPE','G','GLD','PBJ','PBJU','PBJA','PBJS','DPDMIS'}
# Blue = Circuit Court NG/Acquittal
BLUE = {'JAQ','NG'}
# Red = Circuit Court NP/Stet
RED = {'STET','DISM','NP'}

DATE_RE = re.compile(r'^\d{1,2}/\d{1,2}/\d{4}$')
FILENO_RE = re.compile(r'^003-\d+$')

# --- Extract rows from PDF ---
pdf_path = r'c:\Users\Sebastian Grammas\Desktop\MD_County_Case_DF\mpia_update\19to25Felony_All.xlsx - 19to25Felonies.pdf'
doc = fitz.open(pdf_path)

all_rows = []
for page_num in range(len(doc)):
    lines = [l.strip() for l in doc[page_num].get_text().split('\n') if l.strip()]
    header = {'FileNumber','CauseNumber','Stage','CaseStatus','FinalDisp','FinalDispDate'}
    i = 0
    while i < len(lines):
        if lines[i] in header:
            i += 1
            continue
        if FILENO_RE.match(lines[i]):
            row = [lines[i]]
            i += 1
            count = 0
            while count < 5 and i < len(lines):
                if FILENO_RE.match(lines[i]) and count >= 4:
                    break
                row.append(lines[i])
                i += 1
                count += 1
            if len(row) >= 6:
                all_rows.append({'FinalDisp': row[4].strip(), 'FinalDispDate': row[5].strip()})
        else:
            i += 1

# --- Tally by year ---
yearly = defaultdict(lambda: {'yellow': 0, 'blue': 0, 'red': 0})

for row in all_rows:
    date_str = row['FinalDispDate']
    if not DATE_RE.match(date_str):
        continue
    try:
        dt = datetime.strptime(date_str, '%m/%d/%Y')
    except ValueError:
        continue
    year = dt.year
    if year < 2019 or year > 2025:
        continue
    disp = row['FinalDisp']
    if disp in YELLOW:
        yearly[year]['yellow'] += 1
    elif disp in BLUE:
        yearly[year]['blue'] += 1
    elif disp in RED:
        yearly[year]['red'] += 1

# --- Build PDF report ---
output_path = r'c:\Users\Sebastian Grammas\Desktop\MD_County_Case_DF\mpia_update\Felony_Report_2019_2025.pdf'
doc_out = SimpleDocTemplate(
    output_path,
    pagesize=letter,
    rightMargin=inch,
    leftMargin=inch,
    topMargin=inch,
    bottomMargin=inch
)

styles = getSampleStyleSheet()
title_style = ParagraphStyle(
    'Title', parent=styles['Title'],
    fontSize=18, spaceAfter=20, alignment=TA_CENTER, fontName='Helvetica-Bold'
)
heading_style = ParagraphStyle(
    'Heading', parent=styles['Normal'],
    fontSize=13, spaceBefore=14, spaceAfter=6, fontName='Helvetica-Bold'
)
body_style = ParagraphStyle(
    'Body', parent=styles['Normal'],
    fontSize=11, spaceAfter=4, fontName='Helvetica'
)
bold_body_style = ParagraphStyle(
    'BoldBody', parent=styles['Normal'],
    fontSize=11, spaceAfter=4, fontName='Helvetica-Bold'
)
small_italic = ParagraphStyle(
    'SmallItalic', parent=styles['Normal'],
    fontSize=9, fontName='Helvetica-Oblique', spaceAfter=6
)
disclaimer_style = ParagraphStyle(
    'Disclaimer', parent=styles['Normal'],
    fontSize=9, fontName='Helvetica-Bold', spaceAfter=4
)

story = []

story.append(Paragraph("Circuit Court Felony Report – 2019 to 2025", title_style))
story.append(Spacer(1, 0.1 * inch))

description_text = (
    "All non-juvenile circuit court cases disposed of between January 1, 2019 and "
    "December 31, 2025, including associated VOPs disposed of within each respective year. "
    "Each year is reported independently with yearly totals and conviction rates. "
    "Cases are categorized as Circuit Court Conviction (Yellow), Circuit Court NG/Acquittal (Blue), "
    "or Circuit Court NP/Stet (Red) per Defined Terms."
)
story.append(Paragraph(description_text, body_style))
story.append(Spacer(1, 0.15 * inch))

# Grand totals
total_yellow = sum(yearly[y]['yellow'] for y in range(2019, 2026))
total_blue = sum(yearly[y]['blue'] for y in range(2019, 2026))
total_red = sum(yearly[y]['red'] for y in range(2019, 2026))
total_all = total_yellow + total_blue + total_red
overall_rate = round(total_yellow / total_all * 100) if total_all > 0 else 0

# Summary table across all years
story.append(Paragraph("Summary Table (2019–2025)", heading_style))

table_data = [
    ['Year', 'Circuit Court\nConviction', 'Circuit Court\nNG/Acquittal', 'Circuit Court\nNP/Stet', 'Overall\nCases', 'Conviction\nRate']
]
for yr in range(2019, 2026):
    d = yearly[yr]
    total = d['yellow'] + d['blue'] + d['red']
    rate = f"{round(d['yellow'] / total * 100)}%" if total > 0 else "N/A"
    table_data.append([
        str(yr),
        str(d['yellow']),
        str(d['blue']),
        str(d['red']),
        str(total),
        rate
    ])
# Totals row
table_data.append([
    'TOTAL',
    str(total_yellow),
    str(total_blue),
    str(total_red),
    str(total_all),
    f"{overall_rate}%"
])

col_widths = [0.65*inch, 1.15*inch, 1.15*inch, 1.15*inch, 1.0*inch, 1.0*inch]

tbl = Table(table_data, colWidths=col_widths)
tbl.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 9),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f5f5f5')]),
    ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
    ('FONTSIZE', (0, 1), (-1, -2), 10),
    ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#d5e8d4')),
    ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ('FONTSIZE', (0, -1), (-1, -1), 10),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ('TOPPADDING', (0, 0), (-1, -1), 5),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
]))
story.append(tbl)
story.append(Spacer(1, 0.2 * inch))
story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
story.append(Spacer(1, 0.1 * inch))

# Per-year results sections
for yr in range(2019, 2026):
    d = yearly[yr]
    total = d['yellow'] + d['blue'] + d['red']
    rate = round(d['yellow'] / total * 100) if total > 0 else 0

    story.append(Paragraph(f"{yr} Circuit Court Felony Report", title_style))
    story.append(Paragraph("Results:", heading_style))
    story.append(Paragraph(f"Circuit Court Conviction: <b>{d['yellow']}</b>", body_style))
    story.append(Paragraph(f"Circuit Court NG/Acquittal: <b>{d['blue']}</b>", body_style))
    story.append(Paragraph(f"Circuit Court NP/STET: <b>{d['red']}</b>", body_style))
    story.append(Paragraph(f"Circuit Court Overall Cases: <b>{total}</b>", body_style))
    story.append(Paragraph(f"Conviction Rate: <b>{rate}%</b>", body_style))
    story.append(Spacer(1, 0.15 * inch))
    desc = (
        f"All non-juvenile circuit court cases disposed of between January 1, {yr} and "
        f"December 31, {yr}, plus all non-juvenile circuit court cases from {yr} that have "
        f"VOPs that were disposed of in {yr}."
    )
    story.append(Paragraph(desc, small_italic))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(
        "The data contained herein is approximate and generated from an internal case "
        "management system not designed for statistical reporting. It should not be relied upon "
        "as definitive or used for publication or comparative analysis.",
        disclaimer_style
    ))
    if yr < 2025:
        story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
        story.append(Spacer(1, 0.15 * inch))

doc_out.build(story)
print(f"Report saved to: {output_path}")

# Print console summary
print("\nYearly Results (2019–2025):")
print(f"{'Year':<6} {'Conviction':<12} {'NG/Acq':<10} {'NP/Stet':<10} {'Total':<8} {'Conv%'}")
print("-" * 56)
for yr in range(2019, 2026):
    d = yearly[yr]
    total = d['yellow'] + d['blue'] + d['red']
    rate = round(d['yellow'] / total * 100) if total > 0 else 0
    print(f"{yr:<6} {d['yellow']:<12} {d['blue']:<10} {d['red']:<10} {total:<8} {rate}%")
print("-" * 56)
print(f"{'TOTAL':<6} {total_yellow:<12} {total_blue:<10} {total_red:<10} {total_all:<8} {overall_rate}%")
