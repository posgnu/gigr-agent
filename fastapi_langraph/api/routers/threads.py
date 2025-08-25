import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Response
from starlette.status import (
    HTTP_204_NO_CONTENT,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from fastapi_langraph.agent.agent import memory_enabled_agent
from fastapi_langraph.schemas import ThreadHistoryResponse

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/threads", tags=["threads"])


@router.get("/{thread_id}/history")  # type: ignore[misc]
async def get_thread_history(
    thread_id: str,
    limit: Optional[int] = Query(
        50, description="Maximum number of messages to retrieve"
    ),
) -> ThreadHistoryResponse:
    """
    Retrieve conversation history for a specific thread.

    Args:
        thread_id: The thread identifier
        limit: Maximum number of messages to retrieve

    Returns:
        Thread history with messages and metadata
    """
    try:
        # Get thread history from agent
        history = memory_enabled_agent.get_thread_history(thread_id)

        if not history:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND, detail=f"Thread {thread_id} not found"
            )

        # Apply limit
        limited_history = history[:limit] if limit else history

        return ThreadHistoryResponse(
            thread_id=thread_id, history=limited_history, total_messages=len(history)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving thread history: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve thread history",
        )


@router.delete("/{thread_id}", status_code=HTTP_204_NO_CONTENT)  # type: ignore[misc]
async def delete_thread(thread_id: str, response: Response) -> None:
    """
    Delete a specific thread and all its conversation history.

    Args:
        thread_id: The thread identifier to delete

    Returns:
        No content (204) on successful deletion
    """
    try:
        success = memory_enabled_agent.clear_thread(thread_id)

        if not success:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"Thread {thread_id} not found or could not be deleted",
            )

        # Return 204 No Content for successful deletion
        response.status_code = HTTP_204_NO_CONTENT
        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting thread {thread_id}: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete thread"
        )


@router.put("/{thread_id}/clear")  # type: ignore[misc]
async def clear_thread(thread_id: str) -> ThreadHistoryResponse:
    """
    Clear all messages from a specific thread while keeping the thread active.

    Args:
        thread_id: The thread identifier to clear

    Returns:
        Empty thread history response
    """
    try:
        success = memory_enabled_agent.clear_thread(thread_id)

        if not success:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"Thread {thread_id} not found or could not be cleared",
            )

        # Return empty history after clearing
        return ThreadHistoryResponse(thread_id=thread_id, history=[], total_messages=0)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing thread {thread_id}: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to clear thread"
        )


@router.put("/{thread_id}/archive")  # type: ignore[misc]
async def archive_thread(thread_id: str) -> ThreadHistoryResponse:
    """
    Archive a specific thread (placeholder for future implementation).

    Args:
        thread_id: The thread identifier to archive

    Returns:
        Thread history with archived status
    """
    try:
        # Placeholder for future implementation
        # In a real implementation, you would:
        # 1. Mark thread as archived in database
        # 2. Move thread data to archive storage
        # 3. Update thread metadata

        # For now, just return the current history
        history = memory_enabled_agent.get_thread_history(thread_id)

        if not history:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND, detail=f"Thread {thread_id} not found"
            )

        return ThreadHistoryResponse(
            thread_id=thread_id, history=history, total_messages=len(history)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error archiving thread {thread_id}: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to archive thread",
        )
