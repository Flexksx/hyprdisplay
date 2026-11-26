import json
import socket
import subprocess

import pytest
from conftest import DisplaySystem
from hyprland_mock.protocol import Monitor


def monitor(name: str, serial: str) -> Monitor:
    return Monitor(
        name=name,
        available_modes=["1920x1080@60.00Hz", "2560x1440@60.00Hz"],
        make="Acme",
        model="Panel",
        serial=serial,
        width=1920,
        height=1080,
        refresh_rate=60.0,
        x=0,
        y=0,
        scale=1.0,
        transform=0,
    )


def test_connect_positions_monitors_and_disconnect_emits_event(
    display_system: DisplaySystem,
) -> None:
    display_system.connect(monitor("DP-1", "1"))
    display_system.wait_for(
        lambda: display_system.monitors()[0].width == 2560, "first monitor layout"
    )
    with pytest.raises(subprocess.CalledProcessError, match="monitor-connect") as error:
        display_system.connect(monitor("DP-1", "1"))
    assert "already connected" in error.value.stderr
    display_system.connect(monitor("DP-2", "2"))
    display_system.wait_for(lambda: display_system.monitors()[1].x == 2560, "second monitor layout")
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
        listener.settimeout(5)
        listener.connect(str(display_system.sockets / "events.sock"))
        display_system.wait_for(lambda: display_system.listeners() == 2, "event listener")
        display_system.disconnect("DP-2")
        assert listener.recv(1024) == b"monitorremoved>>DP-2\n"
    assert [item.name for item in display_system.monitors()] == ["DP-1"]


def test_repositioned_layout_is_saved_and_restored_after_restart(
    display_system: DisplaySystem,
) -> None:
    display_system.connect(monitor("DP-1", "1"))
    display_system.wait_for(
        lambda: display_system.monitors()[0].width == 2560, "first monitor layout"
    )
    display_system.connect(monitor("DP-2", "2"))
    display_system.wait_for(lambda: display_system.monitors()[1].x == 2560, "second monitor layout")
    display_system.reposition("DP-2", 3000, 120)
    saved = json.loads((display_system.config / "hyprdisplay/layouts.json").read_text())
    assert saved[0]["displays"][1]["settings"]["position"] == {"x": 3000, "y": 120}
    assert (display_system.monitors()[1].x, display_system.monitors()[1].y) == (3000, 120)

    display_system.stop_daemon()
    display_system.disconnect("DP-2")
    display_system.start_daemon()
    display_system.connect(monitor("DP-3", "2"))
    display_system.wait_for(
        lambda: (display_system.monitors()[1].x, display_system.monitors()[1].y) == (3000, 120),
        "saved layout to be restored",
    )
