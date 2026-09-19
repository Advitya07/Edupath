from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongodb_url: str = ""
    mongodb_db: str = "edupath"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    ollama_timeout_seconds: float = 45.0
    pinecone_api_key: str = ""
    pinecone_index: str = ""
    jwt_secret: str = "change-this-for-production"
    # Keep one shared configuration file at the monorepo root when API runs from backend/.
    model_config = SettingsConfigDict(env_file=Path(__file__).resolve().parents[3] / ".env", extra="ignore")

@lru_cache
def get_settings() -> Settings:
    return Settings()
