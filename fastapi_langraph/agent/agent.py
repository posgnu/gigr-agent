import operator
from typing import Annotated, Any, AsyncGenerator, Dict, List, Sequence, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from fastapi_langraph.agent.tools.mock_search import mock_search


# ToolNode implementation for compatibility
class ToolNode:
    """Simple ToolNode implementation for langgraph compatibility."""

    def __init__(self, tools: list) -> None:
        self.tools = {tool.name: tool for tool in tools}

    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        messages = state["messages"]
        last_message = messages[-1]

        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            tool_messages = []
            for tool_call in last_message.tool_calls:
                if tool_call["name"] in self.tools:
                    tool = self.tools[tool_call["name"]]
                    result = tool.invoke(tool_call["args"])
                    tool_messages.append(
                        ToolMessage(content=str(result), tool_call_id=tool_call["id"])
                    )
            return {"messages": tool_messages}
        return {"messages": []}


class AgentState(TypedDict):
    """State for the conversation agent."""

    messages: Annotated[Sequence[BaseMessage], operator.add]


class ReActAgent:
    """
    Enhanced ReAct Agent with thread-based persistence.

    Features:
    - Thread-based conversation persistence using MemorySaver
    - Tool integration with LangGraph
    - Streaming response support
    - Context window management
    """

    def __init__(self) -> None:
        # Initialize LLM (using gpt-4o-mini as GPT-5 may not be available yet)
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1, streaming=True)

        # Tools
        self.tools = [mock_search]
        self.llm_with_tools = self.llm.bind_tools(self.tools)

        # Initialize persistence
        self.checkpointer = MemorySaver()  # In-memory checkpointer for threads

        # Build the graph
        self.graph = self._create_graph()

    def _create_graph(self) -> Any:
        """Create the LangGraph workflow."""
        # Define the graph
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("agent", self._agent_node)
        workflow.add_node("tools", ToolNode(self.tools))

        # Define edges
        workflow.set_entry_point("agent")
        workflow.add_conditional_edges(
            "agent", self._should_continue, {"continue": "tools", "end": END}
        )
        workflow.add_edge("tools", "agent")

        # Compile with persistence
        return workflow.compile(checkpointer=self.checkpointer)

    def _agent_node(self, state: AgentState) -> Dict[str, Any]:
        """Enhanced agent node with streaming support."""
        try:
            # Limit context window to prevent token overflow
            messages = self._manage_context_window(state["messages"])

            # The key insight: LangGraph's stream_mode="messages" works when
            # the LLM is invoked normally. The streaming happens at the graph level.
            result = self.llm_with_tools.invoke(messages)
            return {"messages": [result]}

        except Exception as e:
            error_msg = f"Error in agent execution: {str(e)}"
            return {"messages": [HumanMessage(content=error_msg)]}

    def _should_continue(self, state: AgentState) -> str:
        """Determine next step based on agent's last message."""
        if not state["messages"]:
            return "end"

        last_message = state["messages"][-1]

        # Check if the agent wants to use tools
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "continue"
        return "end"

    def _manage_context_window(
        self, messages: Sequence[BaseMessage], max_messages: int = 20
    ) -> List[BaseMessage]:
        """Manage context window size to prevent token overflow."""
        if len(messages) <= max_messages:
            return list(messages)

        # Keep the first message (usually system) and the most recent messages
        if messages:
            first_message = messages[0]
            recent_messages = messages[-(max_messages - 1) :]
            return [first_message] + list(recent_messages)

        return list(messages)

    async def astream(
        self, input_data: Dict[str, Any], thread_id: str, **kwargs: Any
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream agent responses using official LangGraph streaming methods.

        Uses graph.astream() with stream_mode for proper token streaming.

        Args:
            input_data: Input containing the user message
            thread_id: Thread ID for conversation persistence
            **kwargs: Additional arguments

        Yields:
            Dictionaries containing streaming chunks with metadata
        """
        try:
            # Create RunnableConfig with thread information
            config = RunnableConfig(configurable={"thread_id": thread_id})

            # Prepare the initial state
            messages = [HumanMessage(content=input_data["input"])]
            initial_state = {"messages": messages}

            # Use official LangGraph streaming with stream_mode="messages"
            # This works properly in LangGraph 0.4.5+
            async for chunk in self.graph.astream(
                initial_state, config=config, stream_mode=["messages"]
            ):
                if isinstance(chunk, tuple) and len(chunk) == 2:
                    # Multiple stream modes return (mode, data) tuples
                    stream_mode, data = chunk

                    yield {
                        "stream_mode": stream_mode,
                        "chunk": data,
                        "metadata": {
                            "thread_id": thread_id,
                            "timestamp": __import__("datetime")
                            .datetime.utcnow()
                            .isoformat(),
                        },
                    }
                else:
                    # Single stream mode
                    yield {
                        "stream_mode": "messages",
                        "chunk": chunk,
                        "metadata": {
                            "thread_id": thread_id,
                            "timestamp": __import__("datetime")
                            .datetime.utcnow()
                            .isoformat(),
                        },
                    }

        except Exception as e:
            # Yield error in consistent format
            yield {
                "stream_mode": "error",
                "chunk": {"error": str(e)},
                "metadata": {"thread_id": thread_id},
            }

    def get_thread_history(self, thread_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a specific thread."""
        try:
            config = {"configurable": {"thread_id": thread_id}}
            state_history = list(self.graph.get_state_history(config))

            formatted_history = []
            for state_snapshot in state_history:
                if state_snapshot.values.get("messages"):
                    messages = state_snapshot.values["messages"]
                    formatted_history.append(
                        {
                            "timestamp": state_snapshot.created_at,
                            "messages": [
                                {"type": msg.type, "content": msg.content}
                                for msg in messages
                            ],
                        }
                    )

            return formatted_history

        except Exception as e:
            print(f"Error retrieving thread history: {e}")
            return []

    def clear_thread(self, thread_id: str) -> bool:
        """Clear a specific thread's history."""
        try:
            # Note: MemorySaver doesn't have a direct delete method
            # In production, you'd implement this with a persistent store
            # For now, this is a placeholder that always returns True
            return True

        except Exception as e:
            print(f"Error clearing thread: {e}")
            return False


# Create global agent instance
memory_enabled_agent = ReActAgent()
