import asyncio
import html
from pathlib import Path

from playwright.sync_api import sync_playwright


BASE_DIR = Path(__file__).resolve().parents[2]
FONTS_DIR = BASE_DIR / "fonts"

DEVANAGARI_FONT = (
    FONTS_DIR / "NotoSansDevanagari-VariableFont_wdth,wght.ttf"
)


def clean_text(text: str) -> str:
    text = text.replace("**", "")
    text = text.replace("__", "")
    text = text.replace("`", "")
    return text.strip()


def build_html(title: str, language: str, speech: str) -> str:
    safe_title = html.escape(clean_text(title))
    safe_language = html.escape(language)

    paragraphs = clean_text(speech).splitlines()

    speech_html = "\n".join(
        f"<p>{html.escape(paragraph)}</p>"
        if paragraph.strip()
        else '<div class="spacer"></div>'
        for paragraph in paragraphs
    )

    font_css = ""

    if DEVANAGARI_FONT.exists():
        font_url = DEVANAGARI_FONT.resolve().as_uri()

        font_css = f"""
        @font-face {{
            font-family: "Noto Sans Devanagari";
            src: url("{font_url}") format("truetype");
            font-weight: 100 900;
            font-style: normal;
        }}
        """

    return f"""
    <!DOCTYPE html>
    <html lang="und">
    <head>
        <meta charset="UTF-8">

        <style>
            {font_css}

            @page {{
                size: A4;
                margin: 20mm 18mm;
            }}

            body {{
                font-family:
                    "Noto Sans Devanagari",
                    "Nirmala UI",
                    "Mangal",
                    sans-serif;
                font-size: 12pt;
                line-height: 1.8;
                color: #222;
                overflow-wrap: break-word;
            }}

            h1 {{
                font-size: 20pt;
                text-align: center;
                line-height: 1.5;
                margin-bottom: 12px;
            }}

            .language {{
                text-align: center;
                font-size: 10pt;
                margin-bottom: 24px;
            }}

            p {{
                margin: 0 0 12px;
                white-space: pre-wrap;
            }}

            .spacer {{
                height: 8px;
            }}
        </style>
    </head>

    <body>
        <h1>{safe_title}</h1>
        <div class="language">
            Language: {safe_language}
        </div>
        {speech_html}
    </body>
    </html>
    """


def generate_pdf_sync(
    title: str,
    language: str,
    speech: str,
) -> bytes:
    document = build_html(title, language, speech)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()

        try:
            page = browser.new_page()

            page.set_content(
                document,
                wait_until="load",
            )

            page.evaluate("document.fonts.ready")

            pdf_bytes = page.pdf(
                format="A4",
                print_background=True,
                prefer_css_page_size=True,
            )

            return pdf_bytes

        finally:
            browser.close()


async def generate_pdf(
    title: str,
    language: str,
    speech: str,
) -> bytes:
    return await asyncio.to_thread(
        generate_pdf_sync,
        title,
        language,
        speech,
    )