import argparse
import logging
import os
import socket
from pathlib import Path

from hyprdisplay_daemon.display.adapters import apply_displays, load_displays
from hyprdisplay_daemon.display.domain import Position
from hyprdisplay_daemon.layout.adapters import load_layout, save_layout
from hyprdisplay_daemon.layout.application import connected_layout, reposition_display


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage display layouts.")
    commands = parser.add_subparsers(dest="command")
    reposition = commands.add_parser("reposition")
    reposition.add_argument("connector")
    reposition.add_argument("x", type=int)
    reposition.add_argument("y", type=int)
    args = parser.parse_args()
    if args.command == "reposition":
        layout = reposition_display(
            load_displays, load_layout, save_layout, args.connector, Position(args.x, args.y)
        )
        apply_displays(layout.displays)
        return
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    socket_path = (
        Path(os.environ["XDG_RUNTIME_DIR"])
        / "hypr"
        / os.environ["HYPRLAND_INSTANCE_SIGNATURE"]
        / ".socket2.sock"
    )
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.connect(str(socket_path))
        for event in connection.makefile(encoding="utf-8"):
            name, separator, connector = event.rstrip("\n").partition(">>")
            if separator and name == "monitoradded":
                layout = connected_layout(load_displays, load_layout, connector)
                apply_displays(layout.displays)
    raise ConnectionError("Hyprland event socket closed")


if __name__ == "__main__":
    main()
