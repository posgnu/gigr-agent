from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):  # type: ignore[misc]
    """
    Settings for the application.

    Reads environment variables from a .env file.
    """

    PROJECT_NAME: str = "fastapi-langraph"
    API_V1_STR: str = "/api/v1"
    DESCRIPTION: str | None = None
    OPENAI_API_KEY: str | None = None

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env")


settings = Settings()
