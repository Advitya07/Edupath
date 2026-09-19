from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongodb_url: str = ""
    mongodb_db: str = "edupath"
    gemini_api_keys: str = ""
    use_ollama: bool = False
    ollama_base_url: str = "http://localhost:11434"
    pinecone_api_key: str = ""
    pinecone_index: str = ""
    jwt_secret: str = "change-this-for-production"
    # Keep one shared configuration file at the monorepo root when API runs from backend/.
    model_config = SettingsConfigDict(env_file=Path(__file__).resolve().parents[3] / ".env", extra="ignore")

    @property
    def gemini_keys(self) -> list[str]:
        return [key.strip() for key in self.gemini_api_keys.split(",") if key.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
