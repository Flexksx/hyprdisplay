import importlib
import json
import logging
import socket
import subprocess
from pathlib import Path
from threading import Thread
from unittest.mock import patch

import pytest
from pydantic import ValidationError


def test_monitor_events(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO)
    socket_dir = tmp_path / "hypr" / "session"
    socket_dir.mkdir(parents=True)
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
    monkeypatch.setenv("HYPRLAND_INSTANCE_SIGNATURE", "session")
    daemon = importlib.import_module("hyprdisplay_daemon.main")

    monkeypatch.setattr(daemon, "SOCKET_PATH", socket_dir / ".socket2.sock")
    monitor = {"name": "DP-1", "width": 1920, "height": 1080}
    result = subprocess.CompletedProcess([], 0, stdout=json.dumps([monitor]))
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
        server.bind(str(socket_dir / ".socket2.sock"))
        server.listen()

        def send_events() -> None:
            with server.accept()[0] as connection:
                connection.sendall(
                    b"workspace>>1\nmonitoradded>>DP-1\nmonitoraddedv2>>0,DP-1,Display\n"
                    b"monitorremoved>>DP-1\nmonitorremovedv2>>0,DP-1,Display\n"
                )

        thread = Thread(target=send_events)
        thread.start()
        with (
            patch("hyprdisplay_daemon.main.subprocess.run", return_value=result) as run,
            pytest.raises(ConnectionError, match="event socket closed"),
        ):
            daemon.main()
        thread.join()

    run.assert_called_once_with(
        ["hyprctl", "-j", "monitors", "all"], check=True, capture_output=True, text=True
    )
    assert len(caplog.records) == 2
    assert caplog.records[0].levelno == logging.INFO
    output = caplog.records[0].getMessage()
    assert "Monitor connected: DP-1" in output
    assert json.loads(output.split("\n", 1)[1]) == monitor
    assert caplog.records[1].levelno == logging.INFO
    assert caplog.records[1].getMessage() == "Monitor disconnected: DP-1"


def test_monitor_response_requires_a_string_name(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_RUNTIME_DIR", "/tmp")
    monkeypatch.setenv("HYPRLAND_INSTANCE_SIGNATURE", "session")
    daemon = importlib.import_module("hyprdisplay_daemon.main")

    result = subprocess.CompletedProcess([], 0, stdout='[{"name": 42}]')
    with (
        patch("hyprdisplay_daemon.main.subprocess.run", return_value=result),
        pytest.raises(ValidationError),
    ):
        daemon.report_monitor("DP-1")
