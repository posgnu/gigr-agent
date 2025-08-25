import asyncio
import json
from typing import Optional

import httpx


class ChatClient:
    """
    Chat client with thread management support.

    Features:
    - Thread-based conversation persistence
    - Thread management commands
    - Interactive chat interface
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.current_thread_id: Optional[str] = None

    async def start_session(self) -> None:
        """Start a new chat session."""
        print("🤖 FastAPI LangGraph Chat Client")
        print("=" * 50)

        # Ask if user wants to start a new thread
        new_thread = input("Start new thread? (y/n, default: y): ").strip().lower()
        if new_thread in ["", "y", "yes"]:
            self.current_thread_id = None
            print("🧵 New thread will be created on first message")
        else:
            thread_id = input("Enter existing thread ID: ").strip()
            if thread_id:
                self.current_thread_id = thread_id
                print(f"🧵 Using existing thread: {thread_id[:8]}...")

        print("\n" + "=" * 50)
        print("Available commands:")
        print("  /help     - Show this help message")
        print("  /new      - Start a new thread")
        print("  /history  - Show current thread history")
        print("  /clear    - Clear current thread")
        print("  /delete   - Delete current thread")
        print("  /exit     - Exit the chat")
        print("=" * 50)

    async def send_message(self, message: str) -> None:
        """Send a message and stream the response."""
        try:
            payload = {
                "input": message,
                "thread_id": self.current_thread_id,
                "session_metadata": {
                    "client": "chat_script",
                    "timestamp": asyncio.get_event_loop().time(),
                },
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/stream",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                ) as response:
                    if response.status_code != 200:
                        print(f"❌ Error: {response.status_code}")
                        return

                    print("🤖 Assistant: ", end="", flush=True)

                    async for line in response.aiter_lines():
                        if line.strip():
                            try:
                                data = json.loads(line)

                                # Update thread ID from first response
                                if data.get("type") == "metadata" and data.get(
                                    "thread_id"
                                ):
                                    if not self.current_thread_id:
                                        self.current_thread_id = data["thread_id"]

                                # Print tokens
                                elif data.get("type") == "token":
                                    print(data.get("content", ""), end="", flush=True)

                                # Handle errors
                                elif data.get("type") == "error":
                                    print(
                                        f"\n❌ Error: {data.get('content', 'Unknown error')}"
                                    )

                            except json.JSONDecodeError:
                                continue

                    print()  # New line after response

        except httpx.TimeoutException:
            print("⏰ Request timed out")
        except httpx.RequestError as e:
            print(f"❌ Connection error: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

    async def show_history(self) -> None:
        """Show current thread history."""
        if not self.current_thread_id:
            print("❌ No active thread")
            return

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/threads/{self.current_thread_id}/history"
                )

                if response.status_code == 200:
                    data = response.json()
                    history = data.get("history", [])

                    if not history:
                        print("📜 No conversation history")
                        return

                    print(f"📜 Thread History ({len(history)} entries):")
                    print("-" * 50)

                    for entry in history[-5:]:  # Show last 5 entries
                        messages = entry.get("messages", [])
                        for msg in messages:
                            msg_type = msg.get("type", "unknown")
                            content = msg.get("content", "")[:100]
                            if msg_type == "human":
                                print(f"👤 User: {content}")
                            elif msg_type == "ai":
                                print(f"🤖 Assistant: {content}")
                        print()
                else:
                    print(f"❌ Failed to retrieve history: {response.status_code}")

        except Exception as e:
            print(f"❌ Error retrieving history: {e}")

    async def clear_thread(self) -> None:
        """Clear the current thread."""
        if not self.current_thread_id:
            print("❌ No active thread to clear")
            return

        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.base_url}/threads/{self.current_thread_id}/clear"
                )

                if response.status_code == 200:
                    print("✅ Thread cleared successfully")
                    self.current_thread_id = None
                elif response.status_code == 404:
                    print("❌ Thread not found")
                    self.current_thread_id = None
                else:
                    print(f"❌ Failed to clear thread: {response.status_code}")

        except Exception as e:
            print(f"❌ Error clearing thread: {e}")

    async def delete_thread(self) -> None:
        """Delete the current thread."""
        if not self.current_thread_id:
            print("❌ No active thread to delete")
            return

        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.base_url}/threads/{self.current_thread_id}"
                )

                if response.status_code == 204:
                    print("✅ Thread deleted successfully")
                    self.current_thread_id = None
                elif response.status_code == 404:
                    print("❌ Thread not found")
                    self.current_thread_id = None
                else:
                    print(f"❌ Failed to delete thread: {response.status_code}")

        except Exception as e:
            print(f"❌ Error deleting thread: {e}")

    async def handle_command(self, command: str) -> bool:
        """Handle chat commands. Returns True if command was processed."""
        command = command.strip().lower()

        if command == "/help":
            print("\n📋 Available Commands:")
            print("  /new      - Start a new thread")
            print("  /history  - Show current thread history")
            print("  /clear    - Clear current thread")
            print("  /delete   - Delete current thread")
            print("  /exit     - Exit the chat")
            return True

        elif command == "/new":
            self.current_thread_id = None
            print("🧵 New thread will be created on next message")
            return True

        elif command == "/history":
            await self.show_history()
            return True

        elif command == "/clear":
            await self.clear_thread()
            return True

        elif command == "/delete":
            await self.delete_thread()
            return True

        elif command == "/exit":
            print("👋 Goodbye!")
            return True

        else:
            print(f"❌ Unknown command: {command}")
            print("Type /help for available commands")
            return True

    async def run(self) -> None:
        """Main chat loop."""
        await self.start_session()

        thread_display = (
            self.current_thread_id[:8] + "..." if self.current_thread_id else "None"
        )
        print(f"\n💬 Chat started! (Thread: {thread_display})")
        print("Type your message or use commands starting with '/'")

        while True:
            try:
                user_input = await asyncio.to_thread(input, "\n👤 You: ")

                # Handle commands
                if user_input.startswith("/"):
                    if await self.handle_command(user_input):
                        if user_input.strip().lower() == "/exit":
                            break
                        continue

                # Send regular message
                if user_input.strip():
                    await self.send_message(user_input.strip())

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except EOFError:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")


async def main() -> None:
    """Run the enhanced chat client."""
    client = ChatClient()
    await client.run()


if __name__ == "__main__":
    asyncio.run(main())
