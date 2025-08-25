import operator
from typing import Annotated, Any, AsyncGenerator, Dict, List, Sequence, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from fastapi_langraph.agent.tools.mock_search import mock_search


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
        # Initialize LLM
        self.llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.1, streaming=True)

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
        """Enhanced agent node with context awareness."""
        try:
            # Limit context window to prevent token overflow
            messages = self._manage_context_window(state["messages"])

            # Invoke LLM with managed context
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

    async def astream_events(
        self, input_data: Dict[str, Any], thread_id: str, **kwargs: Any
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream agent events with thread-based persistence.

        Args:
            input_data: Input containing the user message
            thread_id: Thread ID for conversation persistence
            **kwargs: Additional arguments

        Yields:
            Event dictionaries with streaming response data
        """
        try:
            # Create RunnableConfig with thread information
            config = RunnableConfig(configurable={"thread_id": thread_id})

            # Prepare the initial state
            messages = [HumanMessage(content=input_data["input"])]
            initial_state = {"messages": messages}

            # Stream events from the graph
            async for event in self.graph.astream_events(
                initial_state, config=config, version="v1"
            ):
                yield event

        except Exception as e:
            # Yield error event
            yield {"event": "error", "data": {"error": str(e)}, "name": "agent_error"}

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
