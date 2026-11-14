"""
Tessalynt - ReportLab PDF Export Service
Generates professional academic publications, question papers, answer keys,
and flashcard sets adhering to strict typographic and printing standards.
"""
import io
import re
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

# Brand Color Palette
C_PRIMARY = colors.HexColor("#4F46E5")     # Deep Indigo
C_PRIMARY_DARK = colors.HexColor("#1E1B4B")# Midnight Indigo
C_SECONDARY = colors.HexColor("#7C3AED")   # Violet Accent
C_CYAN = colors.HexColor("#0891B2")        # Cyan Knowledge Accent
C_TEXT = colors.HexColor("#1E293B")        # Slate-800 Body text
C_MUTED = colors.HexColor("#64748B")       # Slate-500 Muted text
C_BORDER = colors.HexColor("#E2E8F0")      # Slate-200 Border
C_CARD_BG = colors.HexColor("#F8FAFC")     # Slate-50 Light BG
C_SUCCESS = colors.HexColor("#10B981")     # Emerald Green
C_SUCCESS_BG = colors.HexColor("#ECFDF5")  # Emerald 50
C_WHITE = colors.HexColor("#FFFFFF")


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute total pages and render
    consistent headers, footers, rules, and 'Page X of Y' page numbers.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_decorations(self, page_count):
        self.saveState()
        width, height = A4
        margin = 36 # 0.5 inch

        # Running Header (on pages after page 1)
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(C_PRIMARY)
            self.drawString(margin, height - 26, "TESSALYNT")
            self.setFont("Helvetica", 8)
            self.setFillColor(C_MUTED)
            self.drawString(margin + 58, height - 26, "|   Learn beyond limits   |   Academic Materials")
            
            # Subtle header divider
            self.setStrokeColor(C_BORDER)
            self.setLineWidth(0.5)
            self.line(margin, height - 30, width - margin, height - 30)

        # Running Footer (all pages)
        self.setStrokeColor(C_BORDER)
        self.setLineWidth(0.5)
        self.line(margin, 32, width - margin, 32)

        # Footer Left: Brand & Date
        self.setFont("Helvetica", 7.5)
        self.setFillColor(C_MUTED)
        now_str = datetime.now().strftime("%B %d, %Y")
        self.drawString(margin, 20, f"Generated with Tessalynt AI  •  {now_str}")

        # Footer Right: Page X of Y
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(width - margin, 20, page_str)

        self.restoreState()


def get_tessalynt_styles():
    """Builds a comprehensive stylesheet tuned for academic clarity and dense readability."""
    base_styles = getSampleStyleSheet()

    styles = {
        "Title": ParagraphStyle(
            "TessalyntTitle",
            parent=base_styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=C_PRIMARY_DARK,
            alignment=0, # Left-aligned
            spaceAfter=4
        ),
        "Subtitle": ParagraphStyle(
            "TessalyntSubtitle",
            parent=base_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=C_SECONDARY,
            spaceAfter=12
        ),
        "Heading1": ParagraphStyle(
            "TessalyntH1",
            parent=base_styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=17,
            textColor=C_PRIMARY,
            spaceBefore=12,
            spaceAfter=5,
            keepWithNext=True
        ),
        "Heading2": ParagraphStyle(
            "TessalyntH2",
            parent=base_styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=C_SECONDARY,
            spaceBefore=9,
            spaceAfter=4,
            keepWithNext=True
        ),
        "Heading3": ParagraphStyle(
            "TessalyntH3",
            parent=base_styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=13,
            textColor=C_TEXT,
            spaceBefore=6,
            spaceAfter=3,
            keepWithNext=True
        ),
        "Body": ParagraphStyle(
            "TessalyntBody",
            parent=base_styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=C_TEXT,
            spaceAfter=5
        ),
        "Bullet": ParagraphStyle(
            "TessalyntBullet",
            parent=base_styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=C_TEXT,
            leftIndent=14,
            firstLineIndent=-10,
            spaceAfter=3
        ),
        "Callout": ParagraphStyle(
            "TessalyntCallout",
            parent=base_styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=8.5,
            leading=12,
            textColor=C_PRIMARY_DARK
        ),
        "MetaLabel": ParagraphStyle(
            "TessalyntMetaLabel",
            parent=base_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=C_MUTED
        ),
        "MetaValue": ParagraphStyle(
            "TessalyntMetaVal",
            parent=base_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=C_TEXT
        ),
        "QuestionText": ParagraphStyle(
            "TessalyntQuestion",
            parent=base_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=13.5,
            textColor=C_PRIMARY_DARK,
            spaceAfter=5
        ),
        "OptionText": ParagraphStyle(
            "TessalyntOption",
            parent=base_styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=C_TEXT
        ),
        "Explanation": ParagraphStyle(
            "TessalyntExpl",
            parent=base_styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=C_TEXT
        ),
        "TableHeader": ParagraphStyle(
            "TessalyntTableHeader",
            parent=base_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10.5,
            textColor=C_WHITE
        ),
        "TableCell": ParagraphStyle(
            "TessalyntTableCell",
            parent=base_styles["Normal"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=10,
            textColor=C_TEXT
        ),
        "CodeText": ParagraphStyle(
            "TessalyntCodeText",
            parent=base_styles["Normal"],
            fontName="Courier",
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor("#312E81")
        ),
        "MathDisplay": ParagraphStyle(
            "TessalyntMathDisplay",
            parent=base_styles["Normal"],
            fontName="Helvetica-BoldOblique",
            fontSize=9,
            leading=13,
            textColor=C_PRIMARY_DARK,
            alignment=1, # Centered
            spaceBefore=4,
            spaceAfter=4
        )
    }
    return styles


def _safe_paragraph(text, style):
    """Creates a ReportLab Paragraph, safely falling back to plain escaped text if XML parsing fails."""
    try:
        return Paragraph(text, style)
    except Exception:
        plain_text = re.sub(r"<[^>]+>", "", text)
        safe_plain = plain_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return Paragraph(safe_plain, style)


def _clean_markdown_to_xml(text):
    """Escapes XML entities and transforms Markdown inline syntax into ReportLab tags."""
    if not text:
        return ""

    replacements = {
        "\\delta": "δ",
        "\\Sigma": "Σ",
        "\\Gamma": "Γ",
        "\\to": "→",
        "\\rightarrow": "→",
        "\\leftarrow": "←",
        "\\times": "×",
        "\\in": "∈",
        "\\notin": "∉",
        "\\cup": "∪",
        "\\cap": "∩",
        "\\subseteq": "⊆",
        "\\le": "≤",
        "\\ge": "≥",
        "\\neq": "≠",
        "\\approx": "≈",
        "\\infty": "∞",
        "\\forall": "∀",
        "\\exists": "∃",
        "\\vdash": "⊢",
        "\\models": "⊨",
        "\\circ": "∘",
        "\\cdot": "·",
        "\\sqcup": "␣",
        "\\Box": "□",
        "\\theta": "θ",
        "\\Theta": "Θ",
        "\\Omega": "Ω",
        "\\omega": "ω",
        "\\alpha": "α",
        "\\beta": "β",
        "\\lambda": "λ",
        "\\pi": "π"
    }

    placeholders = []
    def store_token(val):
        idx = len(placeholders)
        token = f"QQQTESSTOKEN{idx}ZZZ"
        placeholders.append((token, val))
        return token

    # 1. Extract Display Math $$ ... $$
    def replace_display_math(match):
        inner = match.group(1).strip()
        for sym, char in replacements.items():
            inner = inner.replace(sym, char)
        safe_inner = inner.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return store_token(f"<b>[Math: {safe_inner}]</b>")

    text = re.sub(r"\$\$([\s\S]*?)\$\$", replace_display_math, text)

    # 2. Extract Inline Math $ ... $
    def replace_inline_math(match):
        inner = match.group(1).strip()
        for sym, char in replacements.items():
            inner = inner.replace(sym, char)
        safe_inner = inner.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return store_token(f"<i><b>{safe_inner}</b></i>")

    text = re.sub(r"\$([^\$\n]+?)\$", replace_inline_math, text)

    # 3. Extract Inline Code ` ... `
    def replace_inline_code(match):
        inner = match.group(1)
        safe_inner = inner.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return store_token(f'<font face="Courier" color="#4F46E5">{safe_inner}</font>')

    text = re.sub(r"`([^`\n]+?)`", replace_inline_code, text)

    # 4. XML entity replacement for remaining prose
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # 5. Bold **text** or __text__
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"__(.+?)__", r"<b>\1</b>", text)

    # 6. Italic *text* or _text_
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    text = re.sub(r"(?<!\w)_(.+?)_(?!\w)", r"<i>\1</i>", text)

    # 7. Restore tokens in order
    for token, val in placeholders:
        text = text.replace(token, val)

    return text


def _parse_markdown_table(table_lines, styles):
    """Converts markdown table lines into a clean ReportLab Table flowable."""
    raw_rows = []
    for line in table_lines:
        line_str = line.strip()
        # Skip markdown separator row like |:---|:---|
        if re.match(r"^\|[\s\-:]+(\|[\s\-:]+)+\|$", line_str):
            continue
        cells = [c.strip() for c in line_str.strip("|").split("|")]
        if cells:
            raw_rows.append(cells)

    if not raw_rows:
        return None

    max_cols = max(len(r) for r in raw_rows)
    normalized_rows = []
    for idx, row in enumerate(raw_rows):
        padded = row + [""] * (max_cols - len(row))
        row_paras = []
        for cell in padded:
            clean_cell = _clean_markdown_to_xml(cell)
            if idx == 0:
                p = _safe_paragraph(f"<b>{clean_cell}</b>", styles["TableHeader"])
            else:
                p = _safe_paragraph(clean_cell, styles["TableCell"])
            row_paras.append(p)
        normalized_rows.append(row_paras)

    total_width = A4[0] - 72 # 523 pt
    col_w = total_width / float(max_cols)

    t = Table(normalized_rows, colWidths=[col_w] * max_cols)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), C_PRIMARY_DARK),
        ('TEXTCOLOR', (0, 0), (-1, 0), C_WHITE),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, C_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [C_WHITE, C_CARD_BG]),
    ]))
    return t


def build_meta_header(title, subject, topic, stream_or_type, learning_level=None):
    """Creates a branded metadata banner table for the document top."""
    styles = get_tessalynt_styles()
    col_width = (A4[0] - 72) / 3.0 # 3 equal columns

    level_display = (learning_level or "University Academic").replace("_", " ").title()
    track_display = f"{stream_or_type or 'Higher Education'} • {level_display}" if learning_level else (stream_or_type or "Higher Education")

    data = [
        [
            Paragraph("SUBJECT", styles["MetaLabel"]),
            Paragraph("TOPIC", styles["MetaLabel"]),
            Paragraph("TRACK / LEARNING LEVEL", styles["MetaLabel"])
        ],
        [
            Paragraph(_clean_markdown_to_xml(subject or "General"), styles["MetaValue"]),
            Paragraph(_clean_markdown_to_xml(topic or "Study Material"), styles["MetaValue"]),
            Paragraph(_clean_markdown_to_xml(track_display), styles["MetaValue"])
        ]
    ]

    t = Table(data, colWidths=[col_width, col_width, col_width])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), C_CARD_BG),
        ('BOX', (0, 0), (-1, -1), 0.75, C_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, C_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    return t


def markdown_to_flowables(md_text, styles):
    """Converts a full markdown document into a list of ReportLab Flowable objects with table and code support."""
    flowables = []
    lines = md_text.split("\n")
    i = 0
    total_lines = len(lines)

    while i < total_lines:
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        # 1. Markdown Table Detection (| ... |)
        if line.startswith("|") and line.endswith("|") and i + 1 < total_lines:
            table_lines = [line]
            i += 1
            while i < total_lines and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            table_flowable = _parse_markdown_table(table_lines, styles)
            if table_flowable:
                flowables.append(Spacer(1, 4))
                flowables.append(table_flowable)
                flowables.append(Spacer(1, 6))
            continue

        # 2. Fenced Code / Mermaid Block Detection (``` ... ```)
        if line.startswith("```"):
            code_type = line[3:].strip().lower()
            code_lines = []
            i += 1
            while i < total_lines and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1 # skip closing ```

            if code_type == "mermaid":
                # Render clean diagram indicator with structured flowchart text
                flowables.append(Spacer(1, 4))
                diag_box = [
                    [Paragraph("<b>VISUAL WORKFLOW / DIAGRAM ARCHITECTURE</b>", styles["MetaLabel"])],
                    [Paragraph("<font face='Courier' color='#312E81'>" + "<br/>".join(_clean_markdown_to_xml(l) for l in code_lines if l.strip()) + "</font>", styles["TableCell"])]
                ]
                t_diag = Table(diag_box, colWidths=[A4[0] - 72])
                t_diag.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#EEF2FF")),
                    ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor("#F5F3FF")),
                    ('BOX', (0, 0), (-1, -1), 0.75, C_PRIMARY),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ]))
                flowables.append(t_diag)
                flowables.append(Spacer(1, 6))
            else:
                # Regular code block
                flowables.append(Spacer(1, 3))
                code_content = "<br/>".join(_clean_markdown_to_xml(l) for l in code_lines)
                t_code = Table([[Paragraph(code_content, styles["CodeText"])]], colWidths=[A4[0] - 72])
                t_code.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
                    ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ]))
                flowables.append(t_code)
                flowables.append(Spacer(1, 5))
            continue

        # 3. Headings
        if line.startswith("# "):
            heading_text = _clean_markdown_to_xml(line[2:].strip())
            flowables.append(_safe_paragraph(heading_text, styles["Title"]))
            flowables.append(Spacer(1, 4))
        elif line.startswith("## "):
            heading_text = _clean_markdown_to_xml(line[3:].strip())
            flowables.append(_safe_paragraph(heading_text, styles["Heading1"]))
            flowables.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER, spaceBefore=1, spaceAfter=4))
        elif line.startswith("### "):
            heading_text = _clean_markdown_to_xml(line[4:].strip())
            flowables.append(_safe_paragraph(heading_text, styles["Heading2"]))
        elif line.startswith("#### "):
            heading_text = _clean_markdown_to_xml(line[5:].strip())
            flowables.append(_safe_paragraph(heading_text, styles["Heading3"]))
        elif line.startswith("- ") or line.startswith("* ") or line.startswith("• "):
            bullet_text = _clean_markdown_to_xml(line[2:].strip())
            flowables.append(_safe_paragraph(f"&bull;&nbsp;&nbsp;{bullet_text}", styles["Bullet"]))
        elif re.match(r"^\d+\.\s+", line):
            num_match = re.match(r"^(\d+\.)\s+(.+)$", line)
            if num_match:
                prefix = num_match.group(1)
                content = _clean_markdown_to_xml(num_match.group(2))
                flowables.append(_safe_paragraph(f"<b>{prefix}</b>&nbsp;&nbsp;{content}", styles["Bullet"]))
            else:
                flowables.append(_safe_paragraph(_clean_markdown_to_xml(line), styles["Body"]))
        elif line.startswith("---") or line.startswith("***"):
            flowables.append(HRFlowable(width="100%", thickness=0.75, color=C_BORDER, spaceBefore=4, spaceAfter=6))
        elif line.startswith(">"):
            callout_text = _clean_markdown_to_xml(line.lstrip("> ").strip())
            t = Table([[_safe_paragraph(f"<b>Note:</b> {callout_text}", styles["Callout"])]], colWidths=[A4[0] - 72])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), C_CARD_BG),
                ('LEFTPADDING', (0,0), (-1,-1), 10),
                ('RIGHTPADDING', (0,0), (-1,-1), 10),
                ('TOPPADDING', (0,0), (-1,-1), 6),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                ('BOX', (0,0), (-1,-1), 0.5, C_PRIMARY),
            ]))
            flowables.append(t)
            flowables.append(Spacer(1, 4))
        else:
            clean_p = _clean_markdown_to_xml(line)
            flowables.append(_safe_paragraph(clean_p, styles["Body"]))

        i += 1
    return flowables


# ==========================================
# 1. ACADEMIC NOTES PDF GENERATOR
# ==========================================
def generate_notes_pdf(title, subject, topic, stream, notes_markdown, learning_level="academic"):
    """Builds a complete, multi-page, publication-grade academic notes PDF with level metadata."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=42,
        bottomMargin=42
    )

    styles = get_tessalynt_styles()
    story = []

    # Title & Branding header
    story.append(Paragraph("TESSALYNT ACADEMIC REPOSITORY", styles["Subtitle"]))
    story.append(Paragraph(_clean_markdown_to_xml(title or topic), styles["Title"]))
    story.append(Spacer(1, 6))

    # Meta banner with learning level
    story.append(build_meta_header(title, subject, topic, stream or "Academic Standard", learning_level=learning_level))
    story.append(Spacer(1, 12))

    # Convert notes markdown
    body_flowables = markdown_to_flowables(notes_markdown, styles)
    story.extend(body_flowables)

    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer.getvalue()
    buffer.seek(0)
    return buffer.getvalue()


# ==========================================
# 2. QUICK REVISION NOTES PDF GENERATOR
# ==========================================
def generate_revision_pdf(title, subject, topic, revision_markdown):
    """Builds a condensed, high-yield Quick Revision PDF for rapid review."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=42,
        bottomMargin=42
    )

    styles = get_tessalynt_styles()
    story = []

    story.append(Paragraph("TESSALYNT QUICK REVISION SHEET", styles["Subtitle"]))
    story.append(Paragraph(_clean_markdown_to_xml(title or f"Revision: {topic}"), styles["Title"]))
    story.append(Spacer(1, 6))

    story.append(build_meta_header(title, subject, topic, "Exam Sprint Revision"))
    story.append(Spacer(1, 12))

    body_flowables = markdown_to_flowables(revision_markdown, styles)
    story.extend(body_flowables)

    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer.getvalue()


# ==========================================
# 3. MCQ QUESTION PAPER PDF GENERATOR
# ==========================================
def generate_mcq_question_paper_pdf(title, subject, topic, questions, difficulty="Standard"):
    """
    Builds an examination question paper for students.
    Answers and explanations are intentionally EXCLUDED.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=42,
        bottomMargin=42
    )

    styles = get_tessalynt_styles()
    story = []

    story.append(Paragraph("TESSALYNT EXAMINATION ASSESSMENT", styles["Subtitle"]))
    story.append(Paragraph(_clean_markdown_to_xml(title or f"MCQ Examination Paper: {topic}"), styles["Title"]))
    story.append(Spacer(1, 6))

    # Exam Info Banner
    story.append(build_meta_header(title, subject, topic, f"Difficulty: {difficulty}"))
    story.append(Spacer(1, 8))

    # Instructions box
    instructions_text = (
        "<b>Examination Instructions:</b> "
        f"This test paper contains {len(questions)} multiple-choice questions. "
        "Each question carries equal marks. Choose the single best answer and mark your response in the provided brackets [   ]."
    )
    t_inst = Table([[Paragraph(instructions_text, styles["Body"])]], colWidths=[A4[0] - 72])
    t_inst.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), C_CARD_BG),
        ('BOX', (0,0), (-1,-1), 0.5, C_BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_inst)
    story.append(Spacer(1, 12))

    # Questions
    col_w = (A4[0] - 72) / 2.0
    for idx, q in enumerate(questions, 1):
        q_elements = []
        q_prompt = f"<b>Q{idx}.</b> {_clean_markdown_to_xml(q.get('question', ''))} &nbsp;&nbsp;&nbsp;&nbsp;<b>[ &nbsp;&nbsp;&nbsp; ]</b>"
        q_elements.append(Paragraph(q_prompt, styles["QuestionText"]))

        opts = q.get("options", {})
        opt_a = opts.get("A", "")
        opt_b = opts.get("B", "")
        opt_c = opts.get("C", "")
        opt_d = opts.get("D", "")

        table_data = [
            [
                Paragraph(f"<b>(A)</b> {_clean_markdown_to_xml(opt_a)}", styles["OptionText"]),
                Paragraph(f"<b>(B)</b> {_clean_markdown_to_xml(opt_b)}", styles["OptionText"])
            ],
            [
                Paragraph(f"<b>(C)</b> {_clean_markdown_to_xml(opt_c)}", styles["OptionText"]),
                Paragraph(f"<b>(D)</b> {_clean_markdown_to_xml(opt_d)}", styles["OptionText"])
            ]
        ]
        opt_table = Table(table_data, colWidths=[col_w, col_w])
        opt_table.setStyle(TableStyle([
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ]))
        q_elements.append(opt_table)
        q_elements.append(Spacer(1, 8))
        q_elements.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER, spaceBefore=2, spaceAfter=6))

        story.append(KeepTogether(q_elements))

    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer.getvalue()


# ==========================================
# 4. MCQ ANSWER KEY & EXPLANATIONS PDF
# ==========================================
def generate_mcq_answer_key_pdf(title, subject, topic, questions, difficulty="Standard"):
    """
    Builds the complete MCQ Solutions & Explanations Manual.
    Includes an Answer Matrix at the top followed by detailed rationales.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=42,
        bottomMargin=42
    )

    styles = get_tessalynt_styles()
    story = []

    story.append(Paragraph("TESSALYNT SOLUTIONS MANUAL", styles["Subtitle"]))
    story.append(Paragraph(_clean_markdown_to_xml(f"Answer Key & Explanations: {topic}"), styles["Title"]))
    story.append(Spacer(1, 6))

    story.append(build_meta_header(title, subject, topic, "Master Solutions & Analysis"))
    story.append(Spacer(1, 10))

    # Answer Matrix Grid at top for quick scoring
    matrix_heading = Paragraph("<b>Quick Answer Matrix:</b>", styles["Heading3"])
    story.append(matrix_heading)

    # 10 columns per row in matrix
    matrix_rows = []
    current_q_row = []
    current_a_row = []
    for idx, q in enumerate(questions, 1):
        current_q_row.append(f"Q{idx}")
        current_a_row.append(q.get("correct_answer", "-"))
        if len(current_q_row) == 10 or idx == len(questions):
            matrix_rows.append(current_q_row)
            matrix_rows.append(current_a_row)
            current_q_row = []
            current_a_row = []

    matrix_table = Table(matrix_rows)
    matrix_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), C_CARD_BG),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, C_BORDER),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TEXTCOLOR', (0, 1), (-1, 1), C_PRIMARY),
    ]))
    story.append(matrix_table)
    story.append(Spacer(1, 14))

    # Detailed Explanations
    story.append(Paragraph("Detailed Explanations & Step-by-Step Rationale", styles["Heading1"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER, spaceBefore=2, spaceAfter=8))

    for idx, q in enumerate(questions, 1):
        q_elements = []
        correct_opt = q.get("correct_answer", "A")
        correct_text = q.get("options", {}).get(correct_opt, "")
        
        q_prompt = f"<b>Q{idx}.</b> {_clean_markdown_to_xml(q.get('question', ''))}"
        q_elements.append(Paragraph(q_prompt, styles["QuestionText"]))

        ans_badge = (
            f"<font color='{C_SUCCESS.hexval()}'><b>Correct Answer: Option ({correct_opt})</b></font> &mdash; "
            f"<b>{_clean_markdown_to_xml(correct_text)}</b>"
        )
        q_elements.append(Paragraph(ans_badge, styles["Body"]))

        expl = q.get("explanation", "No detailed rationale provided.")
        expl_text = f"<b>Explanation:</b> {_clean_markdown_to_xml(expl)}"
        q_elements.append(Paragraph(expl_text, styles["Explanation"]))
        q_elements.append(Spacer(1, 8))
        q_elements.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER, spaceBefore=2, spaceAfter=6))

        story.append(KeepTogether(q_elements))

    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer.getvalue()


# ==========================================
# 5. FLASHCARDS PDF GENERATOR
# ==========================================
def generate_flashcards_pdf(title, subject, topic, flashcards):
    """
    Builds a printable collection of study flashcards in a clean 2-column card layout.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=42,
        bottomMargin=42
    )

    styles = get_tessalynt_styles()
    story = []

    story.append(Paragraph("TESSALYNT FLASHCARD DECK", styles["Subtitle"]))
    story.append(Paragraph(_clean_markdown_to_xml(title or f"Flashcards: {topic}"), styles["Title"]))
    story.append(Spacer(1, 6))

    story.append(build_meta_header(title, subject, topic, f"Total Cards: {len(flashcards)}"))
    story.append(Spacer(1, 12))

    card_width = (A4[0] - 72)

    for idx, card in enumerate(flashcards, 1):
        tag = card.get("tag", "Concept")
        front = card.get("front", "")
        back = card.get("back", "")

        front_p = Paragraph(f"<b>CARD {idx} &bull; {tag.upper()}</b><br/><font color='#1E1B4B' size='10'><b>Q:</b> {_clean_markdown_to_xml(front)}</font>", styles["Body"])
        back_p = Paragraph(f"<font color='#4F46E5'><b>EXPLANATION / ANSWER:</b></font><br/>{_clean_markdown_to_xml(back)}", styles["Body"])

        card_table = Table(
            [[front_p], [back_p]],
            colWidths=[card_width]
        )
        card_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), C_CARD_BG),
            ('BACKGROUND', (0, 1), (-1, 1), C_WHITE),
            ('BOX', (0, 0), (-1, -1), 1, C_BORDER),
            ('LINEBELOW', (0, 0), (-1, 0), 0.75, C_BORDER),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ]))

        story.append(KeepTogether([card_table, Spacer(1, 10)]))

    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer.getvalue()
