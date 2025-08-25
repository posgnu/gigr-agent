from typing import Any, Dict

from fastapi import APIRouter

from fastapi_langraph.core.config import settings

# Create router
router = APIRouter(tags=["system"])


@router.get("/")  # type: ignore[misc]
def read_root() -> Dict[str, str]:
    """Root endpoint returning service information."""
    return {
        "service": "FastAPI LangGraph Agent",
        "version": "1.0.0",
        "status": "operational",
        "documentation": "/docs",
    }


@router.get("/info")  # type: ignore[misc]
def read_info() -> Dict[str, Any]:
    """Get comprehensive service information and capabilities."""
    return {
        "service": {
            "name": settings.PROJECT_NAME.lower().replace(" ", "-"),
            "description": settings.DESCRIPTION or "AI Agent with Thread Persistence",
            "version": "1.0.0",
        },
        "features": {
            "streaming": True,
            "persistence": True,
            "thread_management": True,
        },
        "endpoints": {
            "stream": "/chat/stream",
            "thread_history": "/threads/{thread_id}/history",
            "delete_thread": "/threads/{thread_id}",
            "clear_thread": "/threads/{thread_id}/clear",
            "archive_thread": "/threads/{thread_id}/archive",
        },
    }


@router.get("/health")  # type: ignore[misc]
def health_check() -> Dict[str, Any]:
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "service": settings.PROJECT_NAME, "version": "1.0.0"}
