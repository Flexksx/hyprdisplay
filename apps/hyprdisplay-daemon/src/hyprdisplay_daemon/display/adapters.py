import re
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
from hyprdisplay_daemon.settings import Settings


class HyprlandMonitor(BaseModel):
    model_config = ConfigDict(strict=True, extra="ignore")

    name: str
    available_modes: list[str] = Field(alias="availableModes")
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
        [Settings().hyprctl, "-j", "monitors"], check=True, capture_output=True, text=True
    )
    monitors = TypeAdapter(list[HyprlandMonitor]).validate_json(result.stdout)
    return [
        Display(
            connector=monitor.name,
            available_modes=tuple(parse_mode(mode) for mode in monitor.available_modes),
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


def parse_mode(value: str) -> DisplayMode:
    match = re.fullmatch(r"(\d+)x(\d+)@([\d.]+)Hz", value)
    if match is None:
        raise ValueError(f"Invalid display mode: {value}")
    return DisplayMode(
        DisplayDimensionSize(int(match[1])),
        DisplayDimensionSize(int(match[2])),
        RefreshRate(float(match[3])),
    )


def apply_displays(displays: tuple[Display, ...]) -> None:
    for display in displays:
        settings = display.settings
        mode = settings.mode
        value = (
            f"{display.connector},{mode.width.value}x{mode.height.value}@{mode.refresh_rate.hertz},"
            f"{settings.position.x}x{settings.position.y},{settings.scale.value},"
            f"transform,{ROTATIONS.index(settings.rotation)}"
        )
        subprocess.run(
            [Settings().hyprctl, "keyword", "monitor", value],
            check=True,
            capture_output=True,
            text=True,
        )
