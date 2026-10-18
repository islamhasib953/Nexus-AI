from functools import lru_cache

from pydantic import AnyHttpUrl, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "nexus-ai-api"
    app_version: str = "0.1.0"
    identity_provider: str = "development"
    identity_issuer_url: str = ""
    identity_audience: str = ""
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = Field(default=8000, ge=1, le=65535)
    web_origin: AnyHttpUrl = "http://localhost:5173"
    model_provider: str = "mock"
    model_name: str = "mock-chat"
    llm_primary_model_id: str = "mock-chat"
    llm_fallback_model_ids: str = ""
    llm_timeout_seconds: float = Field(default=20.0, gt=0, le=120)
    llm_max_retries: int = Field(default=1, ge=0, le=3)
    llm_tenant_daily_budget_usd: float = Field(default=0.0, ge=0)
    llm_global_daily_budget_usd: float = Field(default=0.0, ge=0)
    llm_allow_paid_fallback: bool = False
    router_cache_ttl_seconds: int = Field(default=900, ge=0, le=86400)
    router_context_max_chars: int = Field(default=12000, ge=1000, le=100000)
    router_cache_enabled: bool = True
    agent_max_iterations: int = Field(default=3, ge=1, le=10)
    agent_max_tokens: int = Field(default=2048, ge=128, le=16000)
    agent_timeout_seconds: float = Field(default=30.0, gt=0, le=300)
    groq_api_key: str = ""
    groq_base_url: str = "https://api.groq.com/openai/v1"
    huggingface_api_key: str = ""
    huggingface_base_url: str = "https://router.huggingface.co/v1"
    ollama_base_url: str = "http://localhost:11434"
    qdrant_url: str = ""
    qdrant_collection: str = "nexus_chunks"
    mcp_remote_url: str = ""
    tool_rate_limit_per_minute: int = Field(default=30, ge=1, le=1000)
    rag_chunk_size: int = Field(default=900, ge=200, le=4000)
    rag_default_top_k: int = Field(default=5, ge=1, le=20)
    rag_min_score: float = Field(default=0.12, ge=-1, le=1)
    embedding_provider: str = "hash"
    embedding_model_id: str = "hash-embedding-v1"
    embedding_base_url: str = ""
    embedding_api_key: str = ""
    embedding_dimensions: int = Field(default=128, ge=8, le=4096)
    observability_enabled: bool = True
    metrics_window_hours: int = Field(default=24, ge=1, le=720)
    ops_queue_warning_threshold: int = Field(default=10, ge=1, le=10000)
    ops_error_rate_critical_threshold: float = Field(default=0.05, ge=0, le=1)
    ops_tool_failure_critical_threshold: float = Field(default=0.05, ge=0, le=1)
    metrics_retention_days: int = Field(default=30, ge=1, le=3650)
    database_url: str = "sqlite:///./data/nexus.db"
    dev_auth_enabled: bool = True
    dev_auth_secret: str = "development-only-not-for-production"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @model_validator(mode="after")
    def validate_production_boundaries(self) -> "Settings":
        if self.app_env.lower() == "production":
            if self.dev_auth_enabled:
                raise ValueError("Development authentication must be disabled in production.")
            if self.identity_provider == "development":
                raise ValueError("A production identity provider must be configured.")
            if not self.identity_issuer_url or not self.identity_audience:
                raise ValueError("Production identity issuer and audience are required.")
            if self.embedding_provider == "hash":
                raise ValueError("Hash embeddings are not allowed in production.")
        if self.embedding_provider != "hash" and not self.embedding_base_url:
            raise ValueError("A base URL is required for the configured embedding provider.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
