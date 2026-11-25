import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="HYPRDISPLAY_")

    layouts_path: Path = Field(
        default_factory=lambda: Path(
            os.environ.get("XDG_STATE_HOME") or Path.home() / ".local/state"
        )
        / "hyprdisplay"
        / "layouts.json"
    )
    poll_interval: float = Field(default=1.0, gt=0, allow_inf_nan=False)
