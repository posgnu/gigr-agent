from langchain_core.tools import tool


@tool  # type: ignore[misc]
def mock_search(query: str) -> str:
    """A mock search tool that returns a fixed string."""
    if "error" in query.lower():
        raise ValueError("This is a mock error.")
    return f"Search results for '{query}': Mock result."
