from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastapi_langraph.api.routes import api_router
from fastapi_langraph.core.config import settings
from fastapi_langraph.middleware.logging import logging_middleware

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION or "AI Agent with Thread Persistence",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "system", "description": "System information and health checks"},
        {"name": "chat", "description": "Chat streaming and conversation endpoints"},
        {"name": "threads", "description": "Thread management and history operations"},
    ],
)

# Add middleware
app.middleware("http")(logging_middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
