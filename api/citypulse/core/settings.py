from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")

    data_mode: Literal["synthetic", "real"] = "synthetic"
    network: Literal["off", "allowlist"] = "off"
    network_allowlist: str = ""
    llm_provider: Literal["none", "ollama"] = "none"
    ollama_url: str = "http://127.0.0.1:11434"
    db_path: Path = ROOT / "data" / "db" / "citypulse.sqlite"
    max_upload_mb: int = 25

    @property
    def allowed_hosts(self) -> set[str]:
        return {h.strip() for h in self.network_allowlist.split(",") if h.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()
