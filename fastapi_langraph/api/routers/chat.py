import logging
import uuid
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Union

from fastapi import APIRouter, Body
from fastapi.responses import StreamingResponse

from fastapi_langraph.agent.agent import memory_enabled_agent
from fastapi_langraph.schemas import StreamRequest, StreamResponse

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/chat", tags=["chat"])


def serialize_message_object(
    obj: Any,
) -> Union[Dict[str, Any], str, int, float, List[Any]]:
    """
    Safely serialize LangChain message objects to dictionaries.

    Args:
        obj: LangChain message object (ToolMessage, AIMessageChunk, etc.)

    Returns:
        Serializable dictionary representation or primitive type
    """
    if hasattr(obj, "content") and hasattr(obj, "type"):
        # Handle LangChain Message objects
        result = {
            "type": obj.type,
            "content": obj.content,
        }

        # Add specific fields based on message type
        if hasattr(obj, "tool_call_id"):  # ToolMessage
            result["tool_call_id"] = obj.tool_call_id
        if hasattr(obj, "name"):  # ToolMessage or others with name
            result["name"] = getattr(obj, "name", None)
        if hasattr(obj, "id"):  # Message ID
            result["id"] = getattr(obj, "id", None)
        if hasattr(obj, "tool_calls"):  # AIMessage with tool calls
            result["tool_calls"] = getattr(obj, "tool_calls", [])

        return result

    # For non-message objects, try basic serialization
    try:
        if isinstance(obj, (str, int, float, bool, list, dict)):
            return obj
        elif hasattr(obj, "__dict__"):
            return {
                k: v
                for k, v in obj.__dict__.items()
                if isinstance(v, (str, int, float, bool, list, dict))
            }
        else:
            return str(obj)
    except Exception:
        return str(obj)


def safe_serialize_event_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively serialize event data, handling LangChain objects.

    Args:
        data: Event data dictionary

    Returns:
        Serializable dictionary
    """
    if not isinstance(data, dict):
        serialized = serialize_message_object(data)
        # Ensure we return a dict for this function
        if isinstance(serialized, dict):
            return serialized
        else:
            return {"value": serialized}

    result = {}
    for key, value in data.items():
        if hasattr(value, "__class__") and "Message" in value.__class__.__name__:
            # This is a LangChain message object
            result[key] = serialize_message_object(value)
        elif isinstance(value, dict):
            result[key] = safe_serialize_event_data(value)
        elif isinstance(value, list):
            result[key] = [
                (
                    safe_serialize_event_data(item)
                    if isinstance(item, dict)
                    else serialize_message_object(item)
                )
                for item in value
            ]
        else:
            try:
                # Try to include the value if it's JSON serializable
                import json

                json.dumps(value)
                result[key] = value
            except (TypeError, ValueError):
                # If not serializable, convert to string
                result[key] = str(value)

    return result


@router.post("/stream")  # type: ignore[misc]
async def stream_chat(request: StreamRequest = Body(...)) -> StreamingResponse:
    """
    Stream chat responses with thread-based persistence.

    Features:
    - Automatic thread creation if not provided
    - Persistent conversation state
    - Token-level streaming
    - Comprehensive error handling
    - Request/response tracking
    """

    # Generate thread ID if not provided
    thread_id = request.thread_id or str(uuid.uuid4())

    logger.info(f"Processing stream request for thread {thread_id}")

    async def event_stream() -> AsyncGenerator[str, None]:
        """Generate streaming response events."""
        try:
            # Send initial metadata
            metadata_response = StreamResponse(
                type="metadata",
                content=None,
                thread_id=thread_id,
                user_id=None,
                metadata={
                    "request_id": str(uuid.uuid4()),
                    "timestamp": datetime.utcnow().isoformat(),
                    "thread_created": request.thread_id is None,
                },
            )
            yield f"{metadata_response.model_dump_json()}\n"

            # Stream agent responses
            async for chunk in memory_enabled_agent.astream_events(
                input_data={"input": request.input},
                thread_id=thread_id,
                session_metadata=request.session_metadata,
            ):
                # Transform agent output to API response format
                if chunk.get("event") == "on_chat_model_stream":
                    chunk_data = chunk.get("data", {})
                    content_chunk = chunk_data.get("chunk")

                    if (
                        content_chunk
                        and hasattr(content_chunk, "content")
                        and content_chunk.content
                    ):
                        response = StreamResponse(
                            type="token",
                            content=content_chunk.content,
                            thread_id=thread_id,
                            user_id=None,
                            metadata=None,
                        )
                        yield f"{response.model_dump_json()}\n"

                elif chunk.get("event") in ["on_tool_start", "on_tool_end"]:
                    # Safely serialize tool event data
                    safe_metadata = safe_serialize_event_data(chunk.get("data", {}))

                    response = StreamResponse(
                        type="tool_event",
                        content=None,
                        thread_id=thread_id,
                        user_id=None,
                        metadata=safe_metadata,
                    )
                    yield f"{response.model_dump_json()}\n"

                elif chunk.get("event") == "error":
                    error_response = StreamResponse(
                        type="error",
                        content=chunk.get("data", {}).get("error", "Unknown error"),
                        thread_id=thread_id,
                        user_id=None,
                        metadata=None,
                    )
                    yield f"{error_response.model_dump_json()}\n"

            # Send completion metadata
            completion_response = StreamResponse(
                type="metadata",
                content=None,
                thread_id=thread_id,
                user_id=None,
                metadata={
                    "status": "completed",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
            yield f"{completion_response.model_dump_json()}\n"

        except Exception as e:
            logger.error(f"Error in event stream: {e}")
            error_response = StreamResponse(
                type="error",
                content=f"Stream error: {str(e)}",
                thread_id=thread_id,
                user_id=None,
                metadata=None,
            )
            yield f"{error_response.model_dump_json()}\n"

    return StreamingResponse(
        event_stream(),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Thread-ID": thread_id,
        },
    )
