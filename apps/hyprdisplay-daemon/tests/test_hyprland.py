import json
import subprocess
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from hyprdisplay_daemon.display import Rotation, get_displays
from hyprdisplay_daemon.display.adapters import load_displays

MONITOR = {
    "make": "Dell",
    "model": "U2720Q",
    "serial": "123",
    "width": 3840,
    "height": 2160,
    "refreshRate": 59.997,
    "x": -1920,
    "y": 0,
    "scale": 2.0,
    "transform": 1,
    "name": "DP-1",
}


def test_load_displays() -> None:
    result = subprocess.CompletedProcess([], 0, stdout=json.dumps([MONITOR]))
    with patch("hyprdisplay_daemon.display.adapters.subprocess.run", return_value=result) as run:
        displays = get_displays(load_displays)

    run.assert_called_once_with(
        ["hyprctl", "-j", "monitors"], check=True, capture_output=True, text=True
    )
    display = displays[0]
    assert len(displays) == 1
    assert (display.identity.make, display.identity.model, display.identity.serial) == (
        "Dell",
        "U2720Q",
        "123",
    )
    assert (display.settings.mode.width.value, display.settings.mode.height.value) == (3840, 2160)
    assert display.settings.mode.refresh_rate.hertz == 59.997
    assert (display.settings.position.x, display.settings.position.y) == (-1920, 0)
    assert display.settings.scale.value == 2.0
    assert display.settings.rotation == Rotation.CLOCKWISE_270


def test_rejects_flipped_transform() -> None:
    result = subprocess.CompletedProcess([], 0, stdout=json.dumps([{**MONITOR, "transform": 4}]))
    with (
        patch("hyprdisplay_daemon.display.adapters.subprocess.run", return_value=result),
        pytest.raises(ValidationError),
    ):
        load_displays()


def test_command_failure_is_reported() -> None:
    with (
        patch(
            "hyprdisplay_daemon.display.adapters.subprocess.run",
            side_effect=subprocess.CalledProcessError(1, "hyprctl"),
        ),
        pytest.raises(subprocess.CalledProcessError),
    ):
        load_displays()
