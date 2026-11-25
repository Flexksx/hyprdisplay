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
    model_config = ConfigDict(strict=True, extra="ignore")

    name: str
    make: str
    model: str
    serial: str
    width: int
    height: int
    refresh_rate: float = Field(alias="refreshRate")
    x: int
    y: int
    scale: float
    transform: Literal[0, 1, 2, 3, 4, 5, 6, 7]
    disabled: bool = False


ROTATIONS = (
    Rotation.NORMAL,
    Rotation.CLOCKWISE_270,
    Rotation.CLOCKWISE_180,
    Rotation.CLOCKWISE_90,
    Rotation.FLIPPED,
    Rotation.FLIPPED_CLOCKWISE_270,
    Rotation.FLIPPED_CLOCKWISE_180,
    Rotation.FLIPPED_CLOCKWISE_90,
)


def display_from_monitor(monitor: HyprlandMonitor) -> Display:
    return Display(
        identity=DisplayIdentity(
            connector=monitor.name, make=monitor.make, model=monitor.model, serial=monitor.serial
        ),
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


def load_displays() -> list[Display]:
    result = subprocess.run(
        ["hyprctl", "-j", "monitors"], check=True, capture_output=True, text=True
    )
    monitors = TypeAdapter(list[HyprlandMonitor]).validate_json(result.stdout)
    return [display_from_monitor(monitor) for monitor in monitors if not monitor.disabled]


def apply_display(display: Display) -> None:
    settings = display.settings
    mode = settings.mode
    position = settings.position
    rule = (
        f"{display.identity.connector},{mode.width.value}x{mode.height.value}@"
        f"{mode.refresh_rate.hertz},{position.x}x{position.y},{settings.scale.value},"
        f"transform,{ROTATIONS.index(settings.rotation)}"
    )
    result = subprocess.run(
        ["hyprctl", "keyword", "monitor", rule], check=True, capture_output=True, text=True
    )
    if result.stdout.strip() != "ok":
        raise RuntimeError(
            f"Could not configure {display.identity.connector}: {result.stdout.strip()}"
        )
