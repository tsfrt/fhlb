from __future__ import annotations

import logging
from importlib import resources
from pathlib import Path
from typing import ClassVar

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from ..._metadata import app_name, app_slug

# --- Config ---

project_root = Path(__file__).parent.parent.parent.parent.parent
env_file = project_root / ".env"

if env_file.exists():
    load_dotenv(dotenv_path=env_file)


class AppConfig(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=env_file,
        env_prefix=f"{app_slug.upper()}_",
        extra="ignore",
        env_nested_delimiter="__",
    )
    app_name: str = Field(default=app_name)

    # --- Lakehouse ---
    warehouse_id: str = Field(default="688f49c732cf9083")
    catalog: str = Field(default="fhlb")
    schema_name: str = Field(default="des_moines")

    # --- Genie spaces (persona -> space id) ---
    genie_cro: str = Field(default="01f1e82f58f31ef69360c5654f060e7a")
    genie_cfo: str = Field(default="01f1e82f59381a0d83680aca7ee093cb")
    genie_cbo: str = Field(default="01f1e82f598a1038bbd2776cb84eff6d")
    genie_mission: str = Field(default="01f1e82f59c51a89b804c6a7770bf589")
    genie_cio: str = Field(default="01f1e82f5a0716a29a2d96e88d9db4bf")

    # --- AI Gateway ---
    gateway_endpoint: str = Field(default="fhlb-governed-llm")

    # --- Model Serving: Member Early-Warning (classical ML PD model) ---
    early_warning_endpoint: str = Field(default="fhlb-member-credit-risk")

    # --- Briefing engine: "gateway" (Claude via AI Gateway) or "genie_agent"
    # (Genie deep-research agent mode). Overridable per request. ---
    briefing_engine: str = Field(default="gateway")

    # --- Lakebase ---
    lakebase_instance: str = Field(default="fhlb-lakebase")
    lakebase_database: str = Field(default="fhlb_app")

    def genie_space(self, persona: str) -> str:
        return {
            "cro": self.genie_cro,
            "cfo": self.genie_cfo,
            "cbo": self.genie_cbo,
            "mission": self.genie_mission,
            "cio": self.genie_cio,
        }.get(persona, self.genie_cio)

    @property
    def static_assets_path(self) -> Path:
        return Path(str(resources.files(app_slug))).joinpath("__dist__")

    def __hash__(self) -> int:
        return hash(self.app_name)


# --- Logger ---

logger = logging.getLogger(app_name)
