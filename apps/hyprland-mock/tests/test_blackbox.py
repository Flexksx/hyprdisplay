import json
import os
import socket
import subprocess
import time
from collections.abc import Callable
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
MOCK = ROOT / "apps/hyprland-mock/.venv/bin/hyprland-mock"
MOCK_HYPRCTL = ROOT / "apps/hyprland-mock/.venv/bin/hyprland-mock-hyprctl"
DAEMON = ROOT / "apps/hyprdisplay-daemon/.venv/bin/hyprdisplay-daemon"
MONITOR = {
    "name": "DP-1",
    "availableModes": ["1920x1080@60.00Hz", "2560x1440@60.00Hz"],
    "make": "Acme",
    "model": "Panel",
    "serial": "1",
    "width": 1920,
    "height": 1080,
    "refreshRate": 60.0,
    "x": 0,
    "y": 0,
    "scale": 1.0,
    "transform": 0,
}


def wait_for(predicate: Callable[[], bool]) -> None:
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.02)
    pytest.fail("Timed out waiting for process state")


def test_daemon_applies_layout_to_mock(tmp_path: Path) -> None:
    env = os.environ | {
        "HYPRLAND_MOCK_DIR": str(tmp_path / "sockets"),
        "HYPRDISPLAY_EVENT_SOCKET": str(tmp_path / "sockets/events.sock"),
        "HYPRDISPLAY_HYPRCTL": str(MOCK_HYPRCTL),
        "XDG_CONFIG_HOME": str(tmp_path / "config"),
    }

    def command(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(MOCK), *args], env=env, capture_output=True, text=True, check=check
        )

    mock = subprocess.Popen(
        [str(MOCK), "serve"], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    daemon = None
    try:
        wait_for((tmp_path / "sockets/events.sock").exists)
        daemon = subprocess.Popen(
            [str(DAEMON)], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        wait_for(lambda: json.loads(command("status").stdout)["listeners"] == 1)
        invalid = command("monitor-connect", '{"name":"DP-1"}', check=False)
        assert invalid.returncode != 0
        assert "availableModes" in invalid.stderr
        assert json.loads(command("monitors").stdout) == []
        command("monitor-connect", json.dumps(MONITOR))
        wait_for(lambda: json.loads(command("monitors").stdout)[0]["width"] == 2560)
        monitor = json.loads(command("monitors").stdout)[0]
        assert (monitor["height"], monitor["x"], monitor["y"]) == (1440, 0, 0)
        assert command("monitor-connect", json.dumps(MONITOR), check=False).returncode != 0
        second_monitor = MONITOR | {"name": "DP-2", "serial": "2"}
        command("monitor-connect", json.dumps(second_monitor))
        wait_for(lambda: json.loads(command("monitors").stdout)[1]["x"] == 2560)
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
            listener.settimeout(5)
            listener.connect(str(tmp_path / "sockets/events.sock"))
            wait_for(lambda: json.loads(command("status").stdout)["listeners"] == 2)
            command("monitor-disconnect", "DP-2")
            assert listener.recv(1024) == b"monitorremoved>>DP-2\n"
        assert [item["name"] for item in json.loads(command("monitors").stdout)] == ["DP-1"]
        command("monitor-disconnect", "DP-1")
        assert daemon.poll() is None
    finally:
        if daemon is not None:
            daemon.terminate()
            daemon.communicate(timeout=5)
        mock.terminate()
        mock.communicate(timeout=5)
