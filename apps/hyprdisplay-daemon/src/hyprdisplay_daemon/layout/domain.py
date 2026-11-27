from dataclasses import dataclass
from math import ceil

from hyprdisplay_daemon.display.domain import (
    Display,
    DisplayIdentity,
    DisplayScale,
    DisplaySettings,
    Position,
    Rotation,
)


@dataclass(frozen=True, slots=True)
class Layout:
    displays: tuple[Display, ...]

    @property
    def identity(self) -> frozenset[DisplayIdentity]:
        return frozenset(display.identity for display in self.displays)

    def connect(self, display: Display) -> Layout:
        if display.identity in self.identity:
            raise ValueError("Display is already in the layout")
        if not display.available_modes:
            raise ValueError("Display has no available modes")
        mode = max(display.available_modes, key=lambda item: (item.resolution, item.refresh_rate))
        x = max(
            (
                item.settings.position.x
                + (
                    item.settings.mode.height.value
                    if item.settings.rotation in (Rotation.CLOCKWISE_90, Rotation.CLOCKWISE_270)
                    else item.settings.mode.width.value
                )
                / item.settings.scale.value
                for item in self.displays
            ),
            default=0,
        )
        settings = DisplaySettings(mode, Position(ceil(x), 0), DisplayScale(1), Rotation.NORMAL)
        return Layout((*self.displays, display.apply_settings(settings)))

    def update(self, display: Display) -> Layout:
        if display.identity not in self.identity:
            raise ValueError("Display is not in the layout")
        return Layout(
            tuple(
                item.apply_settings(display.settings) if item.identity == display.identity else item
                for item in self.displays
            )
        )
