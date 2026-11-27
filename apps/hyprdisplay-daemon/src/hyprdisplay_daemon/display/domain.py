from dataclasses import dataclass, replace
from enum import IntEnum
from math import isfinite
from typing import override


@dataclass(frozen=True, slots=True)
class DisplayIdentity:
    make: str
    model: str
    serial: str

    def __post_init__(self) -> None:
        if not (self.make.strip() or self.model.strip() or self.serial.strip()):
            raise ValueError("Display identity must not be empty")


@dataclass(frozen=True, slots=True)
class DisplayDimensionSize:
    value: int

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("Display dimension must be non-negative")


@dataclass(frozen=True, slots=True, order=True)
class RefreshRate:
    hertz: float

    def __post_init__(self) -> None:
        if not isfinite(self.hertz) or self.hertz <= 0:
            raise ValueError("Refresh rate must be finite and positive")

    @override
    def __str__(self) -> str:
        return f"{self.hertz}Hz"


@dataclass(frozen=True, slots=True)
class Resolution:
    width: DisplayDimensionSize
    height: DisplayDimensionSize

    def __lt__(self, other: Resolution) -> bool:
        return (self.width.value * self.height.value, self.width.value, self.height.value) < (
            other.width.value * other.height.value,
            other.width.value,
            other.height.value,
        )

    def __gt__(self, other: Resolution) -> bool:
        return other < self


@dataclass(frozen=True, slots=True)
class DisplayMode:
    width: DisplayDimensionSize
    height: DisplayDimensionSize
    refresh_rate: RefreshRate

    @property
    def resolution(self) -> Resolution:
        return Resolution(self.width, self.height)


@dataclass(frozen=True, slots=True)
class Position:
    x: int
    y: int


class Rotation(IntEnum):
    NORMAL = 0
    CLOCKWISE_90 = 90
    CLOCKWISE_180 = 180
    CLOCKWISE_270 = 270


@dataclass(frozen=True, slots=True)
class DisplayScale:
    value: float

    def __post_init__(self) -> None:
        if not isfinite(self.value) or self.value <= 0:
            raise ValueError("Scale must be finite and positive")


@dataclass(frozen=True, slots=True)
class DisplaySettings:
    mode: DisplayMode
    position: Position
    scale: DisplayScale
    rotation: Rotation


@dataclass(frozen=True, slots=True)
class Display:
    identity: DisplayIdentity
    settings: DisplaySettings
    available_modes: tuple[DisplayMode, ...] = ()
    connector: str = ""

    def apply_settings(self, settings: DisplaySettings) -> Display:
        return replace(self, settings=settings)
