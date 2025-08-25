from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from fastapi_langraph.agent.agent import ReActAgent, set_global_agent
from fastapi_langraph.agent.mcp_client import get_mcp_tools_manager
from fastapi_langraph.api.routes import api_router
from fastapi_langraph.core.config import settings
from fastapi_langraph.middleware.logging import logging_middleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("Starting up FastAPI-LangGraph application...")

    try:
        # Initialize MCP tools manager and connect to MCP server
        logger.info("Connecting to MCP server...")
        mcp_manager = await get_mcp_tools_manager()
        mcp_tools = mcp_manager.get_tools()

        if mcp_tools:
            logger.info(f"Successfully loaded {len(mcp_tools)} MCP tools")
            for tool in mcp_tools:
                logger.debug(f"  - {tool.name}: {tool.description[:50]}...")
        else:
            logger.warning("No MCP tools loaded - continuing with local tools only")

        # Initialize the ReActAgent with MCP tools
        agent = ReActAgent(mcp_tools=mcp_tools)
        set_global_agent(agent)

        logger.info("Agent initialized successfully with MCP tools")

    except Exception as e:
        logger.error(f"Failed to initialize MCP tools: {e}")
        logger.info("Falling back to agent without MCP tools")
        # Initialize agent without MCP tools as fallback
        agent = ReActAgent(mcp_tools=None)
        set_global_agent(agent)

    yield

    # Shutdown
    logger.info("Shutting down FastAPI-LangGraph application...")
    try:
        # Clean up MCP connections
        mcp_manager = await get_mcp_tools_manager()
        await mcp_manager.cleanup()
        logger.info("MCP connections cleaned up")
    except Exception as e:
        logger.error(f"Error during MCP cleanup: {e}")


# Create FastAPI app with lifespan
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION
    or "AI Agent with Thread Persistence and MCP Support",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "system", "description": "System information and health checks"},
        {"name": "chat", "description": "Chat streaming and conversation endpoints"},
        {"name": "threads", "description": "Thread management and history operations"},
    ],
    lifespan=lifespan,
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
