"""
Health check router for the AI service.
"""
from fastapi import APIRouter
import os

router = APIRouter()


@router.get("/health")
async def health():
    shopify_api_version = os.getenv("SHOPIFY_API_VERSION", "2026-04")
    ai_service_version = os.getenv("AI_SERVICE_VERSION", "2026.4.0")

    return {
        "status": "healthy",
        "service": "nexusos-ai",
        "version": ai_service_version,
        "shopify_api_version": shopify_api_version,
        "models": {
            "ollama": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            "claude": os.getenv("ANTHROPIC_MODEL", "configured-by-env"),
            "openai": os.getenv("OPENAI_MODEL", "configured-by-env"),
        },
    }
