import json
import logging
import time
from functools import partial
from pathlib import Path

from pydantic import TypeAdapter

from hyprdisplay_daemon.display import apply_displays, get_displays
from hyprdisplay_daemon.display.adapters import (
    HyprlandMonitor,
    apply_display,
    display_from_monitor,
    load_displays,
)
from hyprdisplay_daemon.layout import (
    Layout,
    LoadLayoutsPort,
    SaveLayoutsPort,
    save_layout,
    select_layout,
)
from hyprdisplay_daemon.layout.adapters import read_layouts, save_layouts
from hyprdisplay_daemon.settings import Settings


def migrate_layouts(path: Path) -> None:
    if not path.exists():
        return
    data = path.read_bytes()
    if not isinstance(json.loads(data), dict):
        return
    saved = TypeAdapter(dict[str, list[HyprlandMonitor]]).validate_json(data)
    layouts = [Layout(tuple(display_from_monitor(monitor) for monitor in monitors))
               for monitors in saved.values()]
    save_layouts(path, {layout.identity: layout for layout in layouts})


def update_layout(
    previous: Layout | None, load_saved: LoadLayoutsPort, save_saved: SaveLayoutsPort
) -> Layout:
    current = Layout(tuple(get_displays(load_displays)))
    if not current.displays or current == previous:
        return current
    if previous is None or current.identity != previous.identity:
        target = select_layout(current, previous, load_saved)
        if apply_displays(current.displays, target.displays, apply_display):
            current = Layout(tuple(get_displays(load_displays)))
    save_layout(current, load_saved, save_saved)
    return current


def run(settings: Settings) -> None:
    path = settings.layouts_path
    migrate_layouts(path)
    load_saved = partial(read_layouts, path)
    save_saved = partial(save_layouts, path)
    previous = None
    while True:
        previous = update_layout(previous, load_saved, save_saved)
        time.sleep(settings.poll_interval)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    run(Settings())


if __name__ == "__main__":
    main()
