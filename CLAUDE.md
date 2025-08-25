# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commit Message Guidelines

When creating git commits:
1. Follow Conventional Commits specification (https://www.conventionalcommits.org/en/v1.0.0/)
2. Format: `<type>[optional scope]: <description>`
   - Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`
   - Include `BREAKING CHANGE:` in footer or `!` after type/scope for breaking changes
   - Examples:
     - `feat: add email notifications for new users`
     - `fix(auth): correct password validation regex`
     - `docs: update README with API examples`
     - `feat!: remove deprecated authentication endpoint`
3. Do not include the Claude co-author signature
4. Write clear, concise commit messages without any Claude attribution

## Development Commands

```bash
# Install dependencies
poetry install

# Run development server
poetry run uvicorn fastapi_langraph.main:app --reload

# Run tests
poetry run pytest tests/
poetry run pytest tests/ --cov=fastapi_langraph  # with coverage

# Interactive chat client for testing
poetry run python scripts/chat.py

# Pre-commit hooks (if configured)
poetry run pre-commit install
poetry run pre-commit run --all-files
```

## Architecture Overview

This is a FastAPI application integrating LangGraph for conversational AI with thread-based persistence.

### Core Components

1. **Agent System** (`fastapi_langraph/agent/`)
   - `agent.py`: ReActAgent class with LangGraph state management, tool integration, and thread persistence using MemorySaver
   - Uses GPT-3.5-turbo by default with streaming support
   - Implements context window management (max 20 messages)
   - Tool node integration for extending agent capabilities

2. **API Layer** (`fastapi_langraph/api/`)
   - RESTful endpoints for chat streaming and thread management
   - Main endpoints: `/chat/stream`, `/threads/{thread_id}/history`, `/info`
   - NDJSON streaming format for real-time responses
   - Comprehensive error handling and serialization for LangChain objects

3. **Thread Persistence**
   - In-memory MemorySaver (development) - should be replaced with persistent storage in production
   - Thread-based conversation state management
   - Each thread maintains checkpointed conversation history

4. **Configuration** (`fastapi_langraph/core/config.py`)
   - Environment-based configuration using pydantic-settings
   - Required: `OPENAI_API_KEY`
   - Configurable: `PROJECT_NAME`, `DESCRIPTION`, `LOG_LEVEL`

## Key Patterns

- **Streaming Architecture**: Token-level streaming using AsyncGenerator pattern with NDJSON format
- **State Management**: LangGraph StateGraph with conditional edges for agent-tool interactions
- **Error Handling**: Comprehensive try-catch blocks with error event streaming
- **Message Serialization**: Custom serializers for LangChain message objects to ensure JSON compatibility

## Environment Setup

Create a `.env` file with:
```
OPENAI_API_KEY=your-openai-api-key
PROJECT_NAME=your-project-name
DESCRIPTION=your-project-description
```

## Testing Approach

- Unit tests in `tests/` directory
- Test middleware and logging components
- Use httpx for API endpoint testing
- Interactive testing via `scripts/chat.py` client

## LangGraph Documentation Reference

### Getting Started
- **Main Documentation**: https://langchain-ai.github.io/langgraph/
- **Build a Basic Chatbot**: https://langchain-ai.github.io/langgraph/tutorials/get-started/1-build-basic-chatbot/
- **Workflows & Agents**: https://langchain-ai.github.io/langgraph/tutorials/workflows/
- **Local Server Setup**: https://langchain-ai.github.io/langgraph/tutorials/langgraph-platform/local-server/
- **Agent Overview**: https://langchain-ai.github.io/langgraph/agents/overview/

### Core Concepts & Features
- **Graph API Usage**: https://langchain-ai.github.io/langgraph/how-tos/graph-api/
- **Functional API**: https://langchain-ai.github.io/langgraph/concepts/functional_api/
- **Persistence**: https://langchain-ai.github.io/langgraph/concepts/persistence/
- **Memory Management**: https://langchain-ai.github.io/langgraph/how-tos/memory/add-memory/
- **Streaming**: https://langchain-ai.github.io/langgraph/concepts/streaming/
- **Tools Integration**: https://langchain-ai.github.io/langgraph/concepts/tools/

### Checkpointing & State Management
- **Checkpointing Reference**: https://langchain-ai.github.io/langgraph/reference/checkpoints/
- **Postgres Persistence**: https://langchain-ai.github.io/langgraphjs/how-tos/persistence-postgres/
- **State Management**: Use StateGraph for defining workflows with persistent state

### Human-in-the-Loop
- **Tutorial**: https://langchain-ai.github.io/langgraph/tutorials/get-started/4-human-in-the-loop/
- **Add Human Intervention**: https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/add-human-in-the-loop/
- **Time Travel**: https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/time-travel/

### Advanced Topics
- **Multi-Agent Systems**: https://langchain-ai.github.io/langgraph/agents/multi-agent/
- **Run Agents**: https://langchain-ai.github.io/langgraph/agents/run_agents/
- **Agent Development Guide**: https://langchain-ai.github.io/langgraph/guides/agent-development/

### API Reference & Resources
- **Python API Reference**: https://langchain-ai.github.io/langgraph/reference/
- **JavaScript Version**: https://langchain-ai.github.io/langgraphjs/
- **JavaScript API Reference**: https://langchain-ai.github.io/langgraphjs/reference/
- **JavaScript Concepts**: https://langchain-ai.github.io/langgraphjs/concepts/

### Key LangGraph Features
- **Durable Execution**: Agents persist through failures and auto-resume
- **Memory Types**: Short-term (thread-level) and long-term (cross-thread Store interface)
- **Streaming**: Progressive output display for better UX with LLM latency
- **Production Deployment**: Scalable infrastructure for stateful, long-running workflows
- **Debugging**: LangSmith integration for execution tracing and state monitoring
