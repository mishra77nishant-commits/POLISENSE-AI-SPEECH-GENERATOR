from pathlib import Path
from html import escape
import re
import unicodedata


from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    HRFlowable,
    KeepTogether,
    Table,
    TableStyle,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# =====================================================
# PROJECT PATHS
# =====================================================

BASE_DIR = Path(__file__).resolve().parent.parent
PDF_DIR = BASE_DIR / "generated_pdfs"

PDF_DIR.mkdir(parents=True, exist_ok=True)


# =====================================================
# FONT CONFIGURATION
# =====================================================

def register_fonts():
    """
    Register available TrueType fonts.

    Arial or another Unicode font may improve character coverage.
    Complex scripts such as Hindi may require additional shaping support.
    """

    for regular_path, bold_path in [
        (
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
        ),
        (
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ),
    ]:
        if Path(regular_path).exists():
            try:
                pdfmetrics.registerFont(
                    TTFont("ManifestoRegular", regular_path)
                )

                if Path(bold_path).exists():
                    pdfmetrics.registerFont(
                        TTFont("ManifestoBold", bold_path)
                    )

                return (
                    "ManifestoRegular",
                    "ManifestoBold"
                    if Path(bold_path).exists()
                    else "ManifestoRegular",
                )

            except Exception:
                continue

    return ("Helvetica", "Helvetica-Bold")


REGULAR_FONT, BOLD_FONT = register_fonts()


# =====================================================
# HELPER FUNCTIONS
# =====================================================

def clean_text(value):
    """Normalize text and replace common unsupported punctuation safely."""

    if value is None:
        return ""

    if isinstance(value, (list, tuple)):
        value = "\n".join(str(item) for item in value)
    else:
        value = str(value)

    value = unicodedata.normalize("NFC", value)

    # Use actual Unicode characters (not literal strings such as '\\u2014').
    replacements = {
        chr(0x2010): "-",   # hyphen
        chr(0x2011): "-",   # non-breaking hyphen
        chr(0x2012): "-",   # figure dash
        chr(0x2013): "-",   # en dash
        chr(0x2014): "-",   # em dash
        chr(0x2212): "-",   # minus sign
        chr(0x2018): "'",   # left single quotation mark
        chr(0x2019): "'",   # right single quotation mark
        chr(0x201C): '"',   # left double quotation mark
        chr(0x201D): '"',   # right double quotation mark
        chr(0x2026): "...", # ellipsis
        chr(0x00A0): " ",   # non-breaking space
        chr(0x200B): "",    # zero-width space
        chr(0xFEFF): "",    # byte-order mark
        chr(0xFFFD): "",    # replacement character
    }
    for source_char, replacement_char in replacements.items():
        value = value.replace(source_char, replacement_char)

    # Remove control characters except newline and tab. Keep Unicode letters,
    # combining marks, and joiners so non-English text is not damaged.
    value = "".join(
        char for char in value
        if char in "\n\t"
        or not unicodedata.category(char).startswith("C")
        or char in ("\u200c", "\u200d")
    )

    return value


def safe_paragraph_text(value):
    """Normalize and HTML-escape text before giving it to ReportLab."""

    text = escape(clean_text(value), quote=False)
    return text.replace("\n", "<br/>")


def add_bullet_list(story, items, styles):
    """Render a list using a simple dash instead of a special bullet."""

    if not isinstance(items, list):
        return

    for item in items:
        if isinstance(item, dict):
            item = item.get("text", str(item))

        text = clean_text(item).strip()

        if not text:
            continue

        story.append(
            Paragraph(
                "- " + safe_paragraph_text(text),
                styles["BulletCustom"],
            )
        )


# =====================================================
# MAIN PDF GENERATOR
# =====================================================

def generate_manifesto_pdf(
    manifesto: dict,
    request_data: dict,
    output_path: str,
) -> str:

    if not isinstance(manifesto, dict):
        raise ValueError("Manifesto content must be a dictionary.")

    required_fields = [
        "title",
        "introduction",
        "sections",
        "conclusion",
    ]

    for field in required_fields:
        if field not in manifesto:
            raise ValueError(
                f"Required manifesto field is missing: {field}"
            )

    if not isinstance(manifesto["sections"], list):
        raise ValueError("Manifesto sections must be a list.")

    # -------------------------------------------------
    # COLORS
    # -------------------------------------------------

    try:
        primary_color = colors.HexColor(
            request_data.get("primary_color", "#174A35")
        )
    except (ValueError, TypeError):
        primary_color = colors.HexColor("#174A35")

    gold = colors.HexColor("#C7A45D")
    dark = colors.HexColor("#263238")
    muted = colors.HexColor("#63716B")
    light = colors.HexColor("#F3F6F4")
    white = colors.white

    # -------------------------------------------------
    # OUTPUT DOCUMENT
    # -------------------------------------------------

    output_file = Path(output_path).resolve()
    output_file.parent.mkdir(parents=True, exist_ok=True)

    document = SimpleDocTemplate(
        str(output_file),
        pagesize=A4,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.70 * inch,
        bottomMargin=0.72 * inch,
        title=clean_text(
            manifesto.get("title", "Election Manifesto")
        ),
        author=clean_text(
            request_data.get("party_name", "POLISENSE AI")
        ),
    )

    # -------------------------------------------------
    # TEXT STYLES
    # -------------------------------------------------

    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="CoverParty",
            fontName=BOLD_FONT,
            fontSize=23,
            leading=30,
            alignment=TA_CENTER,
            textColor=primary_color,
            spaceAfter=12,
        )
    )

    styles.add(
        ParagraphStyle(
            name="CoverTitleCustom",
            fontName=BOLD_FONT,
            fontSize=25,
            leading=32,
            alignment=TA_CENTER,
            textColor=dark,
            spaceBefore=20,
            spaceAfter=15,
        )
    )

    styles.add(
        ParagraphStyle(
            name="CoverSubtitle",
            fontName=REGULAR_FONT,
            fontSize=12,
            leading=18,
            alignment=TA_CENTER,
            textColor=muted,
            spaceAfter=12,
        )
    )

    styles.add(
        ParagraphStyle(
            name="CoverDetailsCustom",
            fontName=REGULAR_FONT,
            fontSize=11,
            leading=19,
            alignment=TA_CENTER,
            textColor=dark,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SectionHeadingCustom",
            fontName=BOLD_FONT,
            fontSize=16,
            leading=21,
            textColor=primary_color,
            spaceBefore=13,
            spaceAfter=8,
            keepWithNext=True,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SubheadingCustom",
            fontName=BOLD_FONT,
            fontSize=11,
            leading=15,
            textColor=dark,
            spaceBefore=8,
            spaceAfter=5,
            keepWithNext=True,
        )
    )

    styles.add(
        ParagraphStyle(
            name="BodyCustom",
            fontName=REGULAR_FONT,
            fontSize=10,
            leading=15,
            textColor=dark,
            alignment=TA_LEFT,
            spaceAfter=9,
            splitLongWords=1,
        )
    )

    styles.add(
        ParagraphStyle(
            name="BulletCustom",
            fontName=REGULAR_FONT,
            fontSize=9.5,
            leading=14,
            textColor=dark,
            leftIndent=12,
            firstLineIndent=0,
            spaceAfter=5,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SmallCustom",
            fontName=REGULAR_FONT,
            fontSize=8.5,
            leading=12,
            textColor=muted,
        )
    )

    styles.add(
        ParagraphStyle(
            name="CardHeadingCustom",
            fontName=BOLD_FONT,
            fontSize=10,
            leading=14,
            textColor=primary_color,
            spaceAfter=4,
        )
    )

    story = []

    # -------------------------------------------------
    # PAGE FOOTER
    # -------------------------------------------------

    party_name = clean_text(
        request_data.get("party_name", "POLISENSE AI")
    )

    def draw_footer(canvas, doc):
        canvas.saveState()

        page_width, _ = A4

        canvas.setStrokeColor(gold)
        canvas.setLineWidth(0.8)

        canvas.line(
            document.leftMargin,
            0.48 * inch,
            page_width - document.rightMargin,
            0.48 * inch,
        )

        canvas.setFont(REGULAR_FONT, 8)
        canvas.setFillColor(muted)

        canvas.drawString(
            document.leftMargin,
            0.29 * inch,
            party_name[:70],
        )

        canvas.drawRightString(
            page_width - document.rightMargin,
            0.29 * inch,
            f"Page {doc.page}",
        )

        canvas.restoreState()

    # -------------------------------------------------
    # COVER PAGE
    # -------------------------------------------------

    story.append(Spacer(1, 0.55 * inch))

    story.append(
        HRFlowable(
            width="45%",
            thickness=4,
            color=gold,
            hAlign="CENTER",
            spaceAfter=24,
        )
    )

    story.append(
        Paragraph(
            safe_paragraph_text(
                request_data.get("party_name", "Political Party")
            ),
            styles["CoverParty"],
        )
    )

    tagline = request_data.get("party_tagline")

    if tagline:
        story.append(
            Paragraph(
                safe_paragraph_text(tagline),
                styles["CoverSubtitle"],
            )
        )

    story.append(Spacer(1, 0.25 * inch))

    story.append(
        Paragraph(
            safe_paragraph_text(
                manifesto.get("title", "Election Manifesto")
            ),
            styles["CoverTitleCustom"],
        )
    )

    subtitle = manifesto.get("subtitle")

    if subtitle:
        story.append(
            Paragraph(
                safe_paragraph_text(subtitle),
                styles["CoverSubtitle"],
            )
        )

    story.append(
        HRFlowable(
            width="30%",
            thickness=2,
            color=gold,
            hAlign="CENTER",
            spaceBefore=12,
            spaceAfter=22,
        )
    )

    cover_details = [
        f"Leader: {request_data.get('leader_name', '')}",
        f"Election: {request_data.get('election_type', '')}",
        f"State: {request_data.get('state', '')}",
    ]

    if request_data.get("constituency"):
        cover_details.append(
            f"Constituency: {request_data['constituency']}"
        )

    cover_details.append(
        f"Language: {request_data.get('language', 'English')}"
    )

    for detail in cover_details:
        story.append(
            Paragraph(
                safe_paragraph_text(detail),
                styles["CoverDetailsCustom"],
            )
        )

    story.append(Spacer(1, 0.4 * inch))

    story.append(Spacer(1, 0.15 * inch))

    story.append(
        Paragraph(
            "A vision for progress, opportunity and inclusive development",
            styles["CoverSubtitle"],
        )
    )

    story.append(PageBreak())

    # -------------------------------------------------
    # EXECUTIVE SUMMARY
    # -------------------------------------------------

    story.append(
        Paragraph(
            "EXECUTIVE SUMMARY",
            styles["SectionHeadingCustom"],
        )
    )

    story.append(
        HRFlowable(
            width="100%",
            thickness=1.2,
            color=gold,
            spaceAfter=12,
        )
    )

    add_bullet_list(
        story,
        manifesto.get("executive_summary", []),
        styles,
    )

    # -------------------------------------------------
    # VISION AND INTRODUCTION
    # -------------------------------------------------

    story.append(
        Paragraph(
            "OUR VISION",
            styles["SectionHeadingCustom"],
        )
    )

    vision_statement = manifesto.get("vision_statement")

    if vision_statement:
        story.append(
            Paragraph(
                safe_paragraph_text(vision_statement),
                styles["BodyCustom"],
            )
        )

    story.append(
        Paragraph(
            "Introduction",
            styles["SubheadingCustom"],
        )
    )

    story.append(
        Paragraph(
            safe_paragraph_text(manifesto.get("introduction", "")),
            styles["BodyCustom"],
        )
    )

    # -------------------------------------------------
    # KEY PRIORITIES
    # -------------------------------------------------

    key_issues = request_data.get("key_issues", [])

    if key_issues:
        story.append(
            Paragraph(
                "KEY PRIORITIES",
                styles["SectionHeadingCustom"],
            )
        )

        card_data = []

        for issue in key_issues:
            card_data.append(
                Paragraph(
                    safe_paragraph_text(issue),
                    styles["CardHeadingCustom"],
                )
            )

        # Create a two-column priority grid.
        rows = []

        for index in range(0, len(card_data), 2):
            left = card_data[index]
            right = (
                card_data[index + 1]
                if index + 1 < len(card_data)
                else ""
            )

            rows.append([left, right])

        priority_table = Table(
            rows,
            colWidths=[3.2 * inch, 3.2 * inch],
        )

        priority_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), light),
                ("BOX", (0, 0), (-1, -1), 0.5, gold),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, gold),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ])
        )

        story.append(priority_table)
        story.append(Spacer(1, 12))

    story.append(PageBreak())

    # -------------------------------------------------
    # POLICY SECTIONS
    # -------------------------------------------------

    story.append(
        Paragraph(
            "POLICY COMMITMENTS",
            styles["SectionHeadingCustom"],
        )
    )

    story.append(
        HRFlowable(
            width="100%",
            thickness=1.2,
            color=gold,
            spaceAfter=12,
        )
    )

    sections = manifesto.get("sections", [])

    for index, section in enumerate(sections):

        if not isinstance(section, dict):
            continue

        heading = section.get(
            "heading",
            section.get("title", f"Policy Area {index + 1}"),
        )

        # Avoid keeping an entire long policy section together.
        story.append(
            Paragraph(
                safe_paragraph_text(heading),
                styles["SectionHeadingCustom"],
            )
        )

        problem = section.get("problem")

        if problem:
            story.append(
                Paragraph(
                    "The Challenge",
                    styles["SubheadingCustom"],
                )
            )

            story.append(
                Paragraph(
                    safe_paragraph_text(problem),
                    styles["BodyCustom"],
                )
            )

        content = section.get(
            "content",
            section.get("description", ""),
        )

        if content:
            story.append(
                Paragraph(
                    "Proposed Policy",
                    styles["SubheadingCustom"],
                )
            )

            story.append(
                Paragraph(
                    safe_paragraph_text(content),
                    styles["BodyCustom"],
                )
            )

        proposed_solutions = section.get(
            "proposed_solutions", []
        )

        if proposed_solutions:
            story.append(
                Paragraph(
                    "Proposed Solutions",
                    styles["SubheadingCustom"],
                )
            )

            add_bullet_list(
                story,
                proposed_solutions,
                styles,
            )

        implementation = section.get("implementation", [])

        if implementation:
            story.append(
                Paragraph(
                    "Implementation Roadmap",
                    styles["SubheadingCustom"],
                )
            )

            add_bullet_list(
                story,
                implementation,
                styles,
            )

        outcomes = section.get("expected_outcomes", [])

        if outcomes:
            story.append(
                Paragraph(
                    "Expected Outcomes",
                    styles["SubheadingCustom"],
                )
            )

            add_bullet_list(
                story,
                outcomes,
                styles,
            )

        story.append(
            HRFlowable(
                width="100%",
                thickness=0.5,
                color=gold,
                spaceBefore=7,
                spaceAfter=10,
            )
        )

    # -------------------------------------------------
    # CONCLUSION
    # -------------------------------------------------

    story.append(
        Paragraph(
            "CONCLUSION",
            styles["SectionHeadingCustom"],
        )
    )

    story.append(
        Paragraph(
            safe_paragraph_text(manifesto.get("conclusion", "")),
            styles["BodyCustom"],
        )
    )

    disclaimer = manifesto.get("disclaimer")

    if disclaimer:
        story.append(Spacer(1, 10))

        story.append(
            Paragraph(
                safe_paragraph_text(disclaimer),
                styles["SmallCustom"],
            )
        )

    # -------------------------------------------------
    # BUILD PDF
    # -------------------------------------------------

    document.build(
        story,
        onFirstPage=draw_footer,
        onLaterPages=draw_footer,
    )

    if not output_file.exists() or output_file.stat().st_size == 0:
        raise RuntimeError(
            "PDF file could not be generated successfully."
        )

    return str(output_file)