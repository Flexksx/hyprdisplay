import json
import socket
import subprocess

import pytest
from conftest import PREFERRED_WIDTH, DisplaySystem, monitor


def test_mock_system_runs_without_daemon(mock_system: DisplaySystem) -> None:
    mock_system.connect(monitor("DP-1", "1"))
    assert mock_system.listeners() == 0
    assert [item.name for item in mock_system.monitors()] == ["DP-1"]


def test_connect_positions_monitors_and_disconnect_emits_event(
    display_system: DisplaySystem,
) -> None:
    display_system.connect(monitor("DP-1", "1"))
    display_system.wait_for(
        lambda: display_system.monitors()[0].width == PREFERRED_WIDTH, "first monitor layout"
    )
    with pytest.raises(subprocess.CalledProcessError, match="monitor-connect") as error:
        display_system.connect(monitor("DP-1", "1"))
    assert "already connected" in error.value.stderr
    display_system.connect(monitor("DP-2", "2"))
    display_system.wait_for(
        lambda: display_system.monitors()[1].x == PREFERRED_WIDTH, "second monitor layout"
    )
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
        listener.settimeout(5)
        listener.connect(str(display_system.sockets / "events.sock"))
        display_system.wait_for(lambda: display_system.listeners() == 2, "event listener")
        display_system.disconnect("DP-2")
        assert listener.recv(1024) == b"monitorremoved>>DP-2\n"
    assert [item.name for item in display_system.monitors()] == ["DP-1"]


@pytest.mark.parametrize("x, y", [(3000, 120), (-1920, 0)], ids=["right", "left"])
def test_repositioned_layout_is_saved_and_restored_after_restart(
    display_system: DisplaySystem, x: int, y: int
) -> None:
    layout_path = display_system.config / "custom" / "layouts.json"
    display_system.stop_daemon()
    display_system.environment["HYPRDISPLAY_LAYOUT_PATH"] = str(layout_path)
    display_system.start_daemon()
    display_system.connect(monitor("DP-1", "1"))
    display_system.wait_for(
        lambda: display_system.monitors()[0].width == PREFERRED_WIDTH, "first monitor layout"
    )
    display_system.connect(monitor("DP-2", "2"))
    display_system.wait_for(
        lambda: display_system.monitors()[1].x == PREFERRED_WIDTH, "second monitor layout"
    )
    display_system.reposition("DP-2", x, y)
    saved = json.loads(layout_path.read_text())
    assert not (display_system.config / "hyprdisplay/layouts.json").exists()
    assert all(display["available_modes"] for display in saved[0]["displays"])
    assert saved[0]["displays"][1]["settings"]["position"] == {"x": x, "y": y}
    assert (display_system.monitors()[1].x, display_system.monitors()[1].y) == (x, y)

    display_system.stop_daemon()
    display_system.disconnect("DP-2")
    display_system.start_daemon()
    display_system.connect(monitor("DP-3", "2"))
    display_system.wait_for(
        lambda: (display_system.monitors()[1].x, display_system.monitors()[1].y) == (x, y),
        "saved layout to be restored",
    )


def test_disconnect_restores_layout_for_remaining_monitors(display_system: DisplaySystem) -> None:
    display_system.connect(monitor("DP-1", "1"))
    display_system.wait_for(
        lambda: display_system.monitors()[0].width == PREFERRED_WIDTH, "first layout"
    )
    display_system.reposition("DP-1", 300, 120)
    display_system.connect(monitor("DP-2", "2"))
    display_system.wait_for(
        lambda: (
            len(display_system.monitors()) == 2
            and display_system.monitors()[1].x == 300 + PREFERRED_WIDTH
        ),
        "second layout",
    )
    display_system.reposition("DP-1", 600, 0)
    display_system.disconnect("DP-2")
    display_system.wait_for(
        lambda: (display_system.monitors()[0].x, display_system.monitors()[0].y) == (300, 120),
        "remaining monitor layout to be restored",
    )
    display_system.disconnect("DP-1")
    display_system.connect(monitor("DP-3", "3"))
    display_system.wait_for(
        lambda: display_system.monitors()[0].width == PREFERRED_WIDTH, "reconnected layout"
    )
