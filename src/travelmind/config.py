from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    db_path: Path = Path(os.getenv("TRAVELMIND_DB_PATH", ROOT_DIR / "data" / "travelmind.sqlite3"))
    trace_dir: Path = Path(os.getenv("TRAVELMIND_TRACE_DIR", ROOT_DIR / "traces"))
    overpass_url: str = os.getenv("TRAVELMIND_OVERPASS_URL", "https://overpass-api.de/api/interpreter")
    overpass_timeout_seconds: int = int(os.getenv("TRAVELMIND_OVERPASS_TIMEOUT", "8"))
    llm_api_key: str | None = os.getenv("TRAVELMIND_LLM_API_KEY")
    llm_base_url: str = os.getenv("TRAVELMIND_LLM_BASE_URL", "https://api.deepseek.com/chat/completions")
    llm_model: str = os.getenv("TRAVELMIND_LLM_MODEL", "deepseek-chat")
    llm_timeout_seconds: int = int(os.getenv("TRAVELMIND_LLM_TIMEOUT", "15"))
    nominatim_url: str = os.getenv("TRAVELMIND_NOMINATIM_URL", "https://nominatim.openstreetmap.org/search")


settings = Settings()
