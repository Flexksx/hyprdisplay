import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="HYPRDISPLAY_")

    event_socket: Path | None = None
    hyprctl: str = "hyprctl"

    def event_socket_path(self) -> Path:
        if self.event_socket is not None:
            return self.event_socket
        return (
            Path(os.environ["XDG_RUNTIME_DIR"])
            / "hypr"
            / os.environ["HYPRLAND_INSTANCE_SIGNATURE"]
            / ".socket2.sock"
        )
