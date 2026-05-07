from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    NODE_ENV: str = "development"
    TZ: str = "Asia/Colombo"

    BACKEND_PORT: int = 4000
    BACKEND_PUBLIC_URL: str = "http://localhost:4000"
    JWT_SECRET: str = "change-me"
    ADMIN_BOOTSTRAP_EMAIL: str = "admin@example.com"
    ADMIN_BOOTSTRAP_PASSWORD: str = "change-me"

    DATABASE_URL: str = "postgresql+asyncpg://shop:change-me@postgres:5432/whatsapp_shop"
    REDIS_URL: str = "redis://redis:6379"
    QDRANT_URL: str = "http://qdrant:6333"
    QDRANT_COLLECTION: str = "chat_memory"

    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_VERIFY_TOKEN: str = ""
    WHATSAPP_APP_SECRET: str = ""
    WHATSAPP_API_VERSION: str = "v20.0"

    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-6"
    ANTHROPIC_CLASSIFIER_MODEL: str = "claude-haiku-4-5-20251001"

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    EMBEDDING_PROVIDER: str = "openai"
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    MAX_TURNS_PER_CONVERSATION: int = 20
    RATE_LIMIT_MSG_PER_5MIN: int = 30


settings = Settings()
