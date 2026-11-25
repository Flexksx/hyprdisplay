import subprocess
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from hyprdisplay_daemon.display.domain import (
    Display,
    DisplayDimensionSize,
    DisplayIdentity,
    DisplayMode,
    DisplayScale,
    DisplaySettings,
    Position,
    RefreshRate,
    Rotation,
)


class HyprlandMonitor(BaseModel):
    model_config = ConfigDict(strict=True)

    make: str
    model: str
    serial: str
    width: int
    height: int
    refresh_rate: float = Field(alias="refreshRate")
    x: int
    y: int
    scale: float
    transform: Literal[0, 1, 2, 3]


ROTATIONS = (Rotation.NORMAL, Rotation.CLOCKWISE_270, Rotation.CLOCKWISE_180, Rotation.CLOCKWISE_90)


def load_displays() -> list[Display]:
    result = subprocess.run(
        ["hyprctl", "-j", "monitors"], check=True, capture_output=True, text=True
    )
    monitors = TypeAdapter(list[HyprlandMonitor]).validate_json(result.stdout)
    return [
        Display(
            identity=DisplayIdentity(make=monitor.make, model=monitor.model, serial=monitor.serial),
            settings=DisplaySettings(
                mode=DisplayMode(
                    width=DisplayDimensionSize(monitor.width),
                    height=DisplayDimensionSize(monitor.height),
                    refresh_rate=RefreshRate(monitor.refresh_rate),
                ),
                position=Position(x=monitor.x, y=monitor.y),
                scale=DisplayScale(monitor.scale),
                rotation=ROTATIONS[monitor.transform],
            ),
        )
        for monitor in monitors
    ]
