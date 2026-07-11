"""
Central configuration. Every tunable in one place — no magic numbers.
"""
import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    # Chunking
    chunk_size: int = 400
    chunk_overlap: int = 80
    min_chunk_size: int = 50

    # Retrieval
    top_k: int = 10
    final_k: int = 5
    similarity_threshold: float = 0.25
    low_confidence_threshold: float = 0.40
    rrf_k: int = 60

    # Provider: "openai" or "azure"
    llm_provider: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", "openai").lower())

    # Reranker: "llm" (uses configured LLM) or "crossencoder" (local HuggingFace model)
    reranker_type: str = field(default_factory=lambda: os.getenv("RERANKER_TYPE", "llm").lower())

    # Web loader
    use_playwright_requests: bool = field(default_factory=lambda: os.getenv("USE_PLAYWRIGHT_REQUESTS", "false").lower() == "true")
    # SSL verification: True = verify (default), False = disable (corp proxy bypass),
    # or set REQUESTS_CA_BUNDLE=/path/to/corp-ca.crt to use custom CA cert
    web_ssl_verify: bool = field(default_factory=lambda: os.getenv("WEB_SSL_VERIFY", "true").lower() != "false")

    # LLM — OpenAI
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openai_model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o"))

    # LLM — Azure OpenAI
    azure_openai_api_key: str = field(default_factory=lambda: os.getenv("AZURE_OPENAI_API_KEY", ""))
    azure_openai_endpoint: str = field(default_factory=lambda: os.getenv("AZURE_OPENAI_ENDPOINT", ""))
    azure_openai_api_version: str = field(default_factory=lambda: os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"))
    azure_openai_deployment: str = field(default_factory=lambda: os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"))
    azure_openai_embedding_deployment: str = field(default_factory=lambda: os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-large"))

    max_tokens: int = 1024
    temperature: float = 0.3

    # Memory
    max_turns: int = 10

    # Embedding — OpenAI
    openai_embedding_model: str = field(default_factory=lambda: os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large"))
    embedding_dim: int = 3072

    # Storage — ChromaDB
    chroma_dir: str = "./chroma_db"
    collection_name: str = "rag_chunks"

    # Storage — MongoDB
    mongodb_uri: str = field(default_factory=lambda: os.getenv("MONGODB_URI", "mongodb://localhost:27017"))
    mongodb_db: str = field(default_factory=lambda: os.getenv("MONGODB_DB", "rag_chatbot"))

    # Token budget
    context_tokens: int = 3000
    history_tokens: int = 1000

    # ========== CONFLUENCE INTEGRATION ==========
    confluence_enabled: bool = field(default_factory=lambda: os.getenv("CONFLUENCE_ENABLED", "true").lower() == "true")
    confluence_spaces: list = field(default_factory=lambda: [s.strip() for s in os.getenv("CONFLUENCE_SPACES", "").split(",") if s.strip()])
    confluence_sync_interval_minutes: int = field(default_factory=lambda: int(os.getenv("CONFLUENCE_SYNC_INTERVAL", "5")))
    confluence_tracking_db: str = field(default_factory=lambda: os.getenv("CONFLUENCE_TRACKING_DB", "data/confluence_sync.db"))
    confluence_rate_limit_per_second: float = field(default_factory=lambda: float(os.getenv("CONFLUENCE_RATE_LIMIT", "10")))


settings = Settings()
