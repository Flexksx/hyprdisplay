import json
import logging
import os
import socket
import subprocess
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, TypeAdapter

SOCKET_PATH = (
    Path(os.environ["XDG_RUNTIME_DIR"])
    / "hypr"
    / os.environ["HYPRLAND_INSTANCE_SIGNATURE"]
    / ".socket2.sock"
)


logger = logging.getLogger(__name__)


class MonitorEvent(StrEnum):
    CONNECTED = "monitoradded"
    DISCONNECTED = "monitorremoved"


class HyprlandMonitor(BaseModel):
    model_config = ConfigDict(strict=True, extra="allow")

    name: str


def report_monitor(monitor_name: str) -> None:
    result = subprocess.run(
        ["hyprctl", "-j", "monitors", "all"],
        check=True,
        capture_output=True,
        text=True,
    )
    monitors = TypeAdapter(list[HyprlandMonitor]).validate_json(result.stdout)
    monitor = next((item for item in monitors if item.name == monitor_name), None)
    if monitor is None:
        logger.warning("Monitor connected: %s; configuration unavailable", monitor_name)
    else:
        logger.info(
            "Monitor connected: %s\n%s", monitor_name, json.dumps(monitor.model_dump(), indent=2)
        )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.connect(str(SOCKET_PATH))
        for event in connection.makefile(encoding="utf-8"):
            name, separator, monitor_name = event.rstrip("\n").partition(">>")
            if not separator:
                continue
            match name:
                case MonitorEvent.CONNECTED:
                    report_monitor(monitor_name)
                case MonitorEvent.DISCONNECTED:
                    logger.info("Monitor disconnected: %s", monitor_name)
    raise ConnectionError("Hyprland event socket closed")


if __name__ == "__main__":
    main()
