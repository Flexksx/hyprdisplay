from dataclasses import replace

import pytest

from hyprdisplay_daemon.display.domain import (
    Display,
    DisplayDimensionSize,
    DisplayMode,
    DisplayScale,
    Position,
    RefreshRate,
    Rotation,
)
from hyprdisplay_daemon.layout.domain import Layout


@pytest.mark.parametrize("mode_order", [(0, 1, 2), (2, 1, 0), (1, 0, 2)])
def test_connect_selects_highest_resolution_then_refresh_rate(
    display: Display, mode_order: tuple[int, int, int]
) -> None:
    high_resolution = DisplayMode(
        DisplayDimensionSize(2560), DisplayDimensionSize(1440), RefreshRate(60)
    )
    fastest = replace(high_resolution, refresh_rate=RefreshRate(144))
    modes = (fastest, display.settings.mode, high_resolution)
    display = replace(display, modes=tuple(modes[index] for index in mode_order))

    layout = Layout(()).connect(display)

    assert layout.identity == frozenset({display.identity})
    assert layout.displays[0].settings.mode == fastest
    assert layout.displays[0].settings.position == Position(0, 0)


@pytest.mark.parametrize(
    "rotation, scale, expected_x",
    [
        (Rotation.NORMAL, 1.0, 2020),
        (Rotation.CLOCKWISE_90, 1.0, 1180),
        (Rotation.CLOCKWISE_180, 1.5, 1380),
        (Rotation.CLOCKWISE_270, 1.5, 820),
        (Rotation.NORMAL, 1.3, 1577),
    ],
)
def test_connect_places_display_after_rotated_scaled_displays(
    display: Display, other_display: Display, rotation: Rotation, scale: float, expected_x: int
) -> None:
    mode = DisplayMode(DisplayDimensionSize(1920), DisplayDimensionSize(1080), RefreshRate(60))
    first = replace(
        display,
        settings=replace(
            display.settings,
            mode=mode,
            position=Position(100, 50),
            rotation=rotation,
            scale=DisplayScale(scale),
        ),
    )
    layout = Layout((first,))

    updated = layout.connect(other_display)

    assert updated.displays[1].settings.position == Position(expected_x, 0)
    assert updated.displays[1].settings.rotation == Rotation.NORMAL
    assert updated.displays[1].settings.scale == DisplayScale(1)
    assert layout.displays == (first,)


def test_connect_rejects_duplicate_identity_and_missing_modes(display: Display) -> None:
    with pytest.raises(ValueError, match="already in the layout"):
        Layout((display,)).connect(display)
    with pytest.raises(ValueError, match="no available modes"):
        Layout(()).connect(replace(display, modes=()))


@pytest.mark.parametrize("position", [Position(-200, 300), Position(0, 0), Position(3000, -100)])
def test_reposition_changes_only_selected_display(
    display: Display, other_display: Display, position: Position
) -> None:
    layout = Layout((display, other_display))

    updated = layout.reposition(other_display.identity, position)

    assert updated.displays[0] == display
    assert updated.displays[1].settings.position == position
    assert updated.displays[1].identity == other_display.identity
    assert layout.displays[1] == other_display


def test_reposition_rejects_unknown_identity(display: Display, other_display: Display) -> None:
    with pytest.raises(ValueError, match="not in the layout"):
        Layout((display,)).reposition(other_display.identity, Position(0, 0))
