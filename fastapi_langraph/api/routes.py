from fastapi import APIRouter

from fastapi_langraph.api.routers import chat, system, threads

# Create main API router
api_router = APIRouter()

# Include all routers
api_router.include_router(system.router)
api_router.include_router(chat.router)
api_router.include_router(threads.router)
