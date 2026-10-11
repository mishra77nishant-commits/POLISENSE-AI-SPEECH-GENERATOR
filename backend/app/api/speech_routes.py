import os
import io

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse, StreamingResponse
from groq import Groq

from app.schemas.speech_schemas import SpeechRequest, SpeechResponse
from app.services.pdf_service import generate_pdf


load_dotenv()

router = APIRouter(
    prefix="/api/speech",
    tags=["Speech Generator"],
)

MODEL_NAME = "openai/gpt-oss-120b"


def clean_speech_text(text: str) -> str:
    """Remove common Markdown formatting from generated speech."""
    text = text.replace("**", "")
    text = text.replace("__", "")
    text = text.replace("`", "")
    return text.strip()


@router.post("/generate", response_model=SpeechResponse)
async def generate_speech(request: SpeechRequest):
    """Generate a speech using the Groq AI API."""

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY is missing. Check your backend .env file.",
        )

    key_points_text = (
        "\n".join(f"- {point}" for point in request.key_points)
        if request.key_points
        else "Develop relevant supporting points for the topic."
    )

    prompt = f"""
Create a complete, well-structured speech using the following details.

Topic: {request.topic}
Language: {request.language}
Audience: {request.audience}
Tone: {request.tone}
Target duration: {request.duration_minutes} minutes

Key points to cover:
{key_points_text}

Requirements:
1. Write the entire speech in the requested language.
2. Start with an appropriate greeting and introduction.
3. Explain the topic clearly for the specified audience.
4. Cover all supplied key points naturally.
5. Include practical examples where appropriate.
6. Use smooth transitions between paragraphs.
7. End with a strong conclusion.
8. Do not invent statistics, facts, or citations.
9. Return only the speech content.
"""

    try:
        client = Groq(api_key=api_key)

        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional speechwriter. "
                        "Write clear, engaging and well-organized speeches."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.7,
            max_completion_tokens=5000,
        )

        speech = completion.choices[0].message.content

        if not speech:
            raise HTTPException(
                status_code=502,
                detail="The AI returned an empty speech. Please try again.",
            )

        return SpeechResponse(
            title=f"Speech on {request.topic}",
            language=request.language,
            speech=speech.strip(),
        )

    except HTTPException:
        raise

    except Exception as exc:
        print(f"Groq speech generation error: {exc}")

        raise HTTPException(
            status_code=502,
            detail=(
                "Speech generation failed. Check your Groq API key, "
                "model availability, API quota, and server logs."
            ),
        )


@router.post("/download/txt")
async def download_speech_txt(request: SpeechRequest):
    """Generate a speech and download it as a UTF-8 text file."""

    result = await generate_speech(request)

    content = (
        f"{result.title}\n"
        f"Language: {result.language}\n"
        f"{'=' * 60}\n\n"
        f"{result.speech}\n"
    )

    return PlainTextResponse(
        content=content,
        headers={
            "Content-Disposition": (
                'attachment; filename="polisense_speech.txt"'
            )
        },
        media_type="text/plain; charset=utf-8",
    )


@router.post("/download/pdf")
async def download_speech_pdf(request: SpeechRequest):
    """Generate a speech and return it as a Chromium-rendered PDF."""

    result = await generate_speech(request)

    try:
        pdf_bytes = await generate_pdf(
            title=result.title,
            language=result.language,
            speech=result.speech,
        )

        if not pdf_bytes or not pdf_bytes.startswith(b"%PDF"):
            raise RuntimeError("The PDF renderer returned invalid PDF data.")

        buffer = io.BytesIO(pdf_bytes)
        buffer.seek(0)

        filename = "polisense_speech.pdf"

        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(pdf_bytes)),
                "Cache-Control": "no-store",
            },
        )

    except Exception as exc:
        print(f"PDF generation error: {exc}")

        raise HTTPException(
            status_code=500,
            detail=(
                "PDF generation failed. Check Playwright, Chromium, "
                "font availability, and the backend terminal for details."
            ),
        )