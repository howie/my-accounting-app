"""Application configuration using pydantic-settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = "postgresql://ledgerone:ledgerone@localhost:5432/ledgerone"

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:3001,http://localhost:3002,http://localhost:3003,http://localhost:3004,http://127.0.0.1:3000,http://127.0.0.1:3001,http://127.0.0.1:3002,http://127.0.0.1:3003,http://127.0.0.1:3004"

    # Environment
    environment: str = "development"

    # API
    api_v1_prefix: str = "/api/v1"

    # LLM Configuration
    llm_provider: str = "gemini"  # gemini | claude | ollama

    # Gemini AI
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # Claude AI
    claude_api_key: str = ""
    claude_model: str = "claude-sonnet-4-20250514"

    # Ollama (Local LLM)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    # Feature 012: Telegram Bot
    telegram_bot_token: str = ""
    telegram_webhook_secret: str = ""

    # Feature 012: LINE Bot
    line_channel_secret: str = ""
    line_channel_access_token: str = ""

    # Feature 012: Slack Bot
    slack_bot_token: str = ""
    slack_signing_secret: str = ""
    slack_app_token: str = ""

    # Feature 012: Gmail API (OAuth2)
    google_client_id: str = ""
    google_client_secret: str = ""

    # Feature 012: Encryption key for OAuth tokens
    encryption_key: str = ""

    # Feature 012: Gmail scan interval (seconds, default 6 hours)
    gmail_scan_interval: int = 21600

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
