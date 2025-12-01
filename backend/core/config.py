from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    log_level: str = "INFO"
    
    # Database
    database_url: Optional[str] = None
    redis_url: Optional[str] = None
    
    # ML Model Configuration
    model_path: str = "./ml/models"
    anomaly_threshold: float = 0.7
    batch_size: int = 10000
    
    # Vector Store Configuration
    vector_store_path: str = "./vector_store"
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    chroma_host: str = "chromadb"
    chroma_port: int = 8000
    
    # RAG Configuration
    llm_model: str = "gpt-3.5-turbo"
    openai_api_key: Optional[str] = None
    max_context_length: int = 4000
    top_k_results: int = 5
    
    # Data Processing
    data_path: str = "./data"
    chunk_size: int = 50000
    max_workers: int = 4
    
    # Security
    secret_key: str = "change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Feature Flags
    enable_cadastral_lookup: bool = False
    enable_market_valuation: bool = False
    enable_folio_history: bool = False
    
    # CORS
    cors_origins: list = ["http://localhost:3000", "http://localhost:5173"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
