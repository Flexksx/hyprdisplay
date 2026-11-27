import os
import subprocess
import tempfile
import time
from collections.abc import Callable, Iterator
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path
from typing import IO

import pytest
from mock_hyprland.protocol import ListenerCount, Monitor
from pydantic import TypeAdapter

ROOT = Path(__file__).resolve().parents[1]
MOCK = ROOT / "apps/mock-hyprland/.venv/bin/mock-hyprland"
MOCK_HYPRCTL = ROOT / "apps/mock-hyprland/.venv/bin/mock-hyprland-hyprctl"
DAEMON = ROOT / "apps/hyprdisplay-daemon/.venv/bin/hyprdisplay-daemon"
MONITORS = TypeAdapter(list[Monitor])


def stop_process(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is None:
        process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)


@dataclass
class DisplaySystem:
    environment: dict[str, str]
    sockets: Path
    config: Path
    mock: subprocess.Popen[bytes]
    mock_log: IO[bytes]
    daemon_log: IO[bytes]
    daemon: subprocess.Popen[bytes] | None = None

    def wait_for(self, predicate: Callable[[], bool], description: str) -> None:
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if self.mock.poll() is not None:
                pytest.fail(f"Mock exited: {self.log(self.mock_log)}")
            if self.daemon is not None and self.daemon.poll() is not None:
                pytest.fail(f"Daemon exited: {self.log(self.daemon_log)}")
            if predicate():
                return
            time.sleep(0.05)
        pytest.fail(
            f"Timed out waiting for {description}. "
            f"Mock: {self.log(self.mock_log)} Daemon: {self.log(self.daemon_log)}"
        )

    def log(self, stream: IO[bytes]) -> str:
        stream.flush()
        return Path(stream.name).read_text()

    def command(self, executable: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(executable), *arguments],
            env=self.environment,
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )

    def listeners(self) -> int:
        result = self.command(MOCK, "status")
        return ListenerCount.model_validate_json(result.stdout).listeners

    def start_daemon(self) -> None:
        self.daemon = subprocess.Popen(
            [str(DAEMON)], env=self.environment, stdout=self.daemon_log, stderr=subprocess.STDOUT
        )
        self.wait_for(lambda: self.listeners() == 1, "daemon to connect")

    def stop_daemon(self) -> None:
        if self.daemon is not None:
            stop_process(self.daemon)
            self.daemon = None
            self.wait_for(lambda: self.listeners() == 0, "daemon to disconnect")

    def connect(self, monitor: Monitor) -> None:
        self.command(MOCK, "monitor-connect", monitor.model_dump_json(by_alias=True))

    def disconnect(self, name: str) -> None:
        self.command(MOCK, "monitor-disconnect", name)

    def monitors(self) -> list[Monitor]:
        return MONITORS.validate_json(self.command(MOCK, "monitors").stdout)

    def reposition(self, name: str, x: int, y: int) -> None:
        self.command(DAEMON, "reposition", name, str(x), str(y))


@pytest.fixture
def display_system(tmp_path: Path) -> Iterator[DisplaySystem]:
    with (
        tempfile.TemporaryDirectory(prefix="hyprdisplay-test-") as socket_dir,
        ExitStack() as stack,
    ):
        sockets = Path(socket_dir)
        config = tmp_path / "config"
        environment = os.environ | {
            "MOCK_HYPRLAND_DIR": str(sockets),
            "HYPRDISPLAY_EVENT_SOCKET": str(sockets / "events.sock"),
            "HYPRDISPLAY_HYPRCTL": str(MOCK_HYPRCTL),
            "XDG_CONFIG_HOME": str(config),
        }
        mock_log = stack.enter_context((tmp_path / "mock.log").open("w+b"))
        daemon_log = stack.enter_context((tmp_path / "daemon.log").open("w+b"))
        mock = subprocess.Popen(
            [str(MOCK), "serve"], env=environment, stdout=mock_log, stderr=subprocess.STDOUT
        )
        system = DisplaySystem(environment, sockets, config, mock, mock_log, daemon_log)
        try:
            system.wait_for((sockets / "events.sock").exists, "mock to start")
            system.start_daemon()
            yield system
        finally:
            try:
                system.stop_daemon()
            finally:
                stop_process(mock)
