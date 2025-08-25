from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class StreamRequest(BaseModel):  # type: ignore[misc]
    """Request for streaming chat with thread persistence."""

    input: str = Field(..., description="The user's query for the agent")
    thread_id: Optional[str] = Field(
        None,
        description="Thread ID for conversation persistence. If not provided, a new thread will be created.",
    )
    session_metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional session context and metadata"
    )


class StreamResponse(BaseModel):  # type: ignore[misc]
    """Response for streaming chat events."""

    type: str = Field(
        ...,
        description="Type of response: 'token', 'tool_event', 'error', or 'metadata'",
    )
    content: Optional[str] = Field(None, description="Response content")
    thread_id: Optional[str] = Field(None, description="Thread ID for this response")
    user_id: Optional[str] = Field(
        None, description="User ID associated with this response"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional response metadata"
    )


class ThreadHistoryRequest(BaseModel):  # type: ignore[misc]
    """Request for retrieving thread conversation history."""

    thread_id: str = Field(..., description="Thread ID to retrieve history for")
    limit: Optional[int] = Field(
        50, description="Maximum number of messages to retrieve"
    )


class ThreadHistoryResponse(BaseModel):  # type: ignore[misc]
    """Response containing thread conversation history."""

    thread_id: str = Field(..., description="Thread ID")
    history: List[Dict[str, Any]] = Field(..., description="Conversation history")
    total_messages: int = Field(..., description="Total number of messages in thread")


class ErrorResponse(BaseModel):  # type: ignore[misc]
    """Standard error response format."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    timestamp: str = Field(..., description="Error timestamp")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional error details"
    )
