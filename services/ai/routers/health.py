"""
Health check router for the AI service.
"""
from fastapi import APIRouter
import os

router = APIRouter()


@router.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "nexusos-ai",
        "version": "2026.1.0",
        "models": {
            "ollama": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            "claude": "claude-3-5-sonnet-20241022",
            "openai": "gpt-4o",
        },
    }
