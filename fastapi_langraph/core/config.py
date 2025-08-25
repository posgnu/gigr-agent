from typing import Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    """
    Settings for the application.

    Reads environment variables from a .env file.
    """

    PROJECT_NAME: str = "fastapi-langraph"
    API_V1_STR: str = "/api/v1"
    DESCRIPTION: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # MCP Configuration
    MCP_SERVER_PATH: str = "/Users/posgnu/repo/gigr-db-mcp"
    MCP_SERVER_URL: Optional[str] = (
        None  # Set to e.g. "http://localhost:8080/mcp" if using HTTP transport
    )

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env")


settings = Settings()
