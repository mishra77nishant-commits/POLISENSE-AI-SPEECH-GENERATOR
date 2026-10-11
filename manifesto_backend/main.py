import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from models.manifesto_request import ManifestoRequest
from services.ai_service import generate_manifesto_content
from utils.pdf_generator import generate_manifesto_pdf


# ==========================================
# APPLICATION CONFIGURATION
# ==========================================

app = FastAPI(
    title="POLISENSE AI - Manifesto Generator",
    description="AI-powered Political Manifesto Generator with PDF Export",
    version="1.0.0",
)


# ==========================================
# DIRECTORY CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent
PDF_DIR = BASE_DIR / "generated_pdfs"
PDF_DIR.mkdir(parents=True, exist_ok=True)


# ==========================================
# CORS CONFIGURATION
# ==========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# HOME ENDPOINT
# ==========================================

@app.get("/")
def home():
    return {
        "status": "success",
        "message": "POLISENSE AI Manifesto Generator Backend is running!",
        "version": "1.0.0",
    }


# ==========================================
# HEALTH CHECK
# ==========================================

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Manifesto Generator",
    }


# ==========================================
# AVAILABLE LANGUAGES
# ==========================================

@app.get("/languages")
def get_languages():
    return {
        "languages": [
            "English",
            "Hindi",
            "Bengali",
            "Tamil",
            "Telugu",
            "Marathi",
            "Gujarati",
            "Kannada",
            "Malayalam",
            "Punjabi",
            "Urdu",
        ]
    }


# ==========================================
# GENERATE MANIFESTO CONTENT
# ==========================================

@app.post("/generate-manifesto")
def generate_manifesto(request: ManifestoRequest):
    try:
        request_data = request.model_dump()

        # Generate manifesto content using Groq AI.
        generated_content = generate_manifesto_content(request_data)

        return {
            "status": "success",
            "message": "Manifesto generated successfully!",
            "leader_name": request.leader_name,
            "party_name": request.party_name,
            "language": request.language,
            "manifesto": generated_content,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Manifesto generation failed: {error}",
        ) from error


# ==========================================
# GENERATE AND DOWNLOAD MANIFESTO PDF
# ==========================================

@app.post("/generate-manifesto-pdf")
def generate_manifesto_pdf_endpoint(request: ManifestoRequest):
    # Generate a unique filename for each PDF request.
    unique_id = uuid.uuid4().hex[:12]
    pdf_path = PDF_DIR / f"manifesto_{unique_id}.pdf"

    try:
        request_data = request.model_dump()

        # STEP 1: Generate manifesto content using Groq AI.
        manifesto_content = generate_manifesto_content(request_data)

        # STEP 2: Generate the PDF. Images are not required by this endpoint.
        generate_manifesto_pdf(
            manifesto=manifesto_content,
            request_data=request_data,
            output_path=str(pdf_path),
        )

        # STEP 3: Prepare a safe download filename.
        safe_party_name = "".join(
            character
            if character.isalnum() or character in "-_"
            else "_"
            for character in request.party_name
        ).strip("_")

        if not safe_party_name:
            safe_party_name = "Political_Party"

        download_filename = f"{safe_party_name}_Manifesto.pdf"

        # STEP 4: Return the PDF as a downloadable response.
        return FileResponse(
            path=str(pdf_path),
            media_type="application/pdf",
            filename=download_filename,
        )

    except ValueError as error:
        if pdf_path.exists():
            pdf_path.unlink()

        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except Exception as error:
        if pdf_path.exists():
            pdf_path.unlink()

        raise HTTPException(
            status_code=500,
            detail=f"PDF generation failed: {error}",
        ) from error
