import sys
import asyncio

# Fix Playwright subprocess support on Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(
        asyncio.WindowsProactorEventLoopPolicy()
    )

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.speech_routes import router as speech_router


app = FastAPI(
    title="POLISENSE AI Speech Generator",
    description=(
        "AI-powered speech generation API "
        "for the POLISENSE AI platform."
    ),
    version="1.0.0",
)


# Enable CORS for local development and deployed Vercel frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://polisense-ai-speech-generator.vercel.app",
        "https://polisense-ai-speech-generator-aur4118j3-polisence.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def home():
    return {
        "message": "POLISENSE AI Speech Generator Backend is Running!",
        "status": "success",
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "speech-generator",
    }


app.include_router(speech_router)