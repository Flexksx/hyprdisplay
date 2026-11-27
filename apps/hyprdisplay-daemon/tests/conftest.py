from collections.abc import Callable

import pytest

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


@pytest.fixture
def make_display() -> Callable[[str], Display]:
    def make(serial: str) -> Display:
        mode = DisplayMode(DisplayDimensionSize(1920), DisplayDimensionSize(1080), RefreshRate(60))
        return Display(
            identity=DisplayIdentity("Acme", "Panel", serial),
            settings=DisplaySettings(mode, Position(0, 0), DisplayScale(1), Rotation.NORMAL),
            modes=(mode,),
            connector=serial,
        )

    return make


@pytest.fixture
def display(make_display: Callable[[str], Display]) -> Display:
    return make_display("first")


@pytest.fixture
def other_display(make_display: Callable[[str], Display]) -> Display:
    return make_display("second")
