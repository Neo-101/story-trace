import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # Application Paths
    BASE_DIR: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    OUTPUT_DIR: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent / "output")
    INPUTS_DIR: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent / "inputs")
    
    # Database
    DATABASE_URL: str = "sqlite:///storytrace.db"
    
    # Server
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # LLM - OpenRouter
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_MODEL: str = "google/gemini-2.0-flash-001"
    
    # LLM - Local
    LOCAL_LLM_BASE_URL: str = "http://localhost:11434/v1"
    LOCAL_LLM_MODEL: str = "qwen2.5:14b"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore" # Ignore extra env vars
    )

    @property
    def database_path(self) -> str:
        """Resolve database path relative to BASE_DIR if it's a relative sqlite path"""
        if self.DATABASE_URL.startswith("sqlite:///"):
            db_path = self.DATABASE_URL.replace("sqlite:///", "")
            if not os.path.isabs(db_path):
                return f"sqlite:///{self.BASE_DIR / db_path}"
        return self.DATABASE_URL

settings = Settings()
