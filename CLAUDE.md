# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

```bash
# Install dependencies
poetry install

# Run development server
poetry run uvicorn fastapi_langraph.main:app --reload
poetry run uvicorn fastapi_langraph.main:app --reload --port 8001  # Alternative port

# Run tests
poetry run pytest tests/
poetry run pytest tests/ --cov=fastapi_langraph  # with coverage
poetry run pytest tests/middleware/test_logging.py -v  # specific test

# Code quality
poetry run black fastapi_langraph/  # Format code
poetry run isort fastapi_langraph/  # Sort imports
poetry run pre-commit install  # Install pre-commit hooks
poetry run pre-commit run --all-files  # Run all pre-commit checks

# Interactive testing
poetry run python scripts/chat.py  # Interactive chat client
```

## Architecture Overview

This is a FastAPI application integrating LangGraph for conversational AI with thread-based persistence and real-time streaming.

### Core Architecture Flow

```
Client Request → FastAPI Router → ReActAgent → LangGraph StateGraph → Tool Execution → Streaming Response
                      ↓                              ↓
                Thread Manager              MemorySaver (Persistence)
```

### Key Components

1. **Agent System** (`fastapi_langraph/agent/agent.py`)
   - `ReActAgent` class implementing LangGraph-based conversational AI
   - Uses `gpt-4o-mini` model with temperature 0.1 for consistency
   - Context window management: automatically truncates at 20 messages
   - Custom `ToolNode` implementation for LangGraph compatibility
   - Streaming via `graph.astream()` with `stream_mode=["messages"]`

2. **API Layer** (`fastapi_langraph/api/`)
   - Modular router structure: `chat`, `threads`, `system`
   - NDJSON (Newline Delimited JSON) streaming format
   - Response types: "token", "metadata", "error"
   - Thread ID auto-generation if not provided
   - Custom serialization for LangChain message objects

3. **Persistence Strategy**
   - `MemorySaver` for in-memory thread persistence (development only)
   - Thread-based checkpointing with `RunnableConfig`
   - Note: `clear_thread()` is placeholder - always returns True
   - Production requires replacing with SqliteSaver or PostgresSaver

4. **Configuration** (`fastapi_langraph/core/config.py`)
   - Environment-based using pydantic-settings
   - Required: `OPENAI_API_KEY`
   - Optional: `PROJECT_NAME`, `DESCRIPTION`, `LOG_LEVEL`

## Critical Implementation Details

### LangGraph Streaming Pattern
```python
# The streaming implementation uses official LangGraph methods:
async for chunk in self.graph.astream(
    initial_state,
    config=config,
    stream_mode=["messages"]  # Critical: enables token-level streaming
):
    # Handle tuple responses (message_chunk, metadata) in LangGraph 0.4.5+
    if isinstance(chunk, tuple) and len(chunk) == 2:
        message_chunk, chunk_metadata = chunk
```

### Message Serialization Complexity
- `serialize_message_object()`: Handles LangChain message objects (ToolMessage, AIMessageChunk, etc.)
- `safe_serialize_event_data()`: Recursive serialization with JSON compatibility checks
- Fallback to string conversion for non-serializable objects

### StateGraph Configuration
```python
# Agent state uses TypedDict with operator.add for message accumulation
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]

# Graph structure: agent → conditional edge → tools → agent
workflow.add_conditional_edges(
    "agent", self._should_continue, {"continue": "tools", "end": END}
)
```

### Context Window Management
- Preserves first message (usually system prompt)
- Keeps most recent 19 messages
- Prevents token overflow with GPT models

## Known Issues & Limitations

1. **Persistence**: In-memory storage lost on restart - production needs persistent backend
2. **Docker Path**: Dockerfile references `./src/fastapi_langraph` but should be `./fastapi_langraph`
3. **CORS Policy**: Wide open (`allow_origins=["*"]`) - needs restriction in production
4. **Thread Archiving**: Placeholder implementation - always returns success
5. **Rate Limiting**: Not implemented - needed for production

## Testing Strategy

- Unit tests for middleware components
- Interactive testing via `scripts/chat.py` client
- API testing with httpx for async endpoints
- Pre-commit hooks ensure code quality (black, isort, ruff, mypy)

## Environment Setup

Create `.env` file:
```
OPENAI_API_KEY=your-openai-api-key
PROJECT_NAME=FastAPI-LangGraph
DESCRIPTION=LangGraph Agent with Streaming
LOG_LEVEL=INFO
```

## Production Migration Checklist

1. Replace `MemorySaver` with persistent storage (SQLite/PostgreSQL)
2. Implement proper authentication middleware
3. Configure CORS for specific origins
4. Add rate limiting and request size constraints
5. Fix Docker build path in Dockerfile
6. Implement proper thread archiving
7. Add monitoring and APM integration

## Commit Message Guidelines

Follow Conventional Commits specification:
- Format: `<type>[optional scope]: <description>`
- Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`
- Examples:
  - `feat: add email notifications for new users`
  - `fix(agent): correct context window management`
  - `docs: update API documentation`
- Do not include Claude co-author signature

## LangGraph Documentation Reference

### Essential Resources
- [Main Documentation](https://langchain-ai.github.io/langgraph/)
- [Streaming Concepts](https://langchain-ai.github.io/langgraph/concepts/streaming/)
- [Persistence](https://langchain-ai.github.io/langgraph/concepts/persistence/)
- [Tools Integration](https://langchain-ai.github.io/langgraph/concepts/tools/)
- [StateGraph API](https://langchain-ai.github.io/langgraph/how-tos/graph-api/)

### Key LangGraph Features Used
- **StateGraph**: Workflow definition with conditional edges
- **MemorySaver**: Thread-based conversation persistence
- **Stream Modes**: Token-level streaming with metadata
- **Tool Nodes**: Integration of external tools in workflow
- **Checkpointing**: Conversation state management
