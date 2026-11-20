import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "NexusAI Enterprise Multi-Agent RAG Platform"
    API_V1_STR: str = "/api"
    ENVIRONMENT: str = "production"
    DEBUG: bool = False

    # Security
    JWT_SECRET: str = "nexusai_super_secret_production_key_change_in_env_2026_xyz"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    # Database
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/nexusai"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Google Gemini GenAI SDK
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-3.5-flash"
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-001"
    EMBEDDING_DIMENSION: int = 768

    # Ingestion & Chunking
    DEFAULT_CHUNK_SIZE: int = 800
    DEFAULT_CHUNK_OVERLAP: int = 150
    MAX_FILE_SIZE_MB: int = 50

    # Retrieval
    DEFAULT_TOP_K: int = 5
    HYBRID_ALPHA: float = 0.5  # 0.0 = full keyword, 1.0 = full vector
    SIMILARITY_THRESHOLD: float = 0.35

    # Multi-Agent Workflow
    MAX_AGENT_RETRIES: int = 2
    MAX_WORKFLOW_CYCLES: int = 4

    # Storage (local vs GCS)
    STORAGE_TYPE: str = "local"  # "local" or "gcs"
    UPLOAD_DIR: str = "./uploads"
    GCS_BUCKET_NAME: Optional[str] = None

    # Pricing per 1M tokens (USD)
    COST_PER_1M_INPUT_TOKENS: float = 0.15   # Gemini 2.5 Flash input
    COST_PER_1M_OUTPUT_TOKENS: float = 0.60  # Gemini 2.5 Flash output
    COST_PER_1M_EMBEDDING_TOKENS: float = 0.025


settings = Settings()
