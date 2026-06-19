from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        protected_namespaces=()
    )

    app_name: str = "TrustLens"
    api_prefix: str = "/api"
    environment: str = "development"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"])

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-1.5-pro"

    pinecone_api_key: str | None = None
    pinecone_index_name: str = "trustlens-agreements"
    pinecone_namespace: str = "default"

    mongodb_uri: str | None = None
    mongodb_database: str = "trustlens"

    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
