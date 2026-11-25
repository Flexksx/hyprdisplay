from typing import Protocol

from hyprdisplay_daemon.display.domain import DisplayIdentity
from hyprdisplay_daemon.layout.domain import Layout


class LoadLayoutsPort(Protocol):
    def __call__(self) -> dict[frozenset[DisplayIdentity], Layout]: ...


class SaveLayoutsPort(Protocol):
    def __call__(self, layouts: dict[frozenset[DisplayIdentity], Layout]) -> None: ...


def select_layout(
    current: Layout, previous: Layout | None, load_layouts: LoadLayoutsPort
) -> Layout:
    saved = load_layouts().get(current.identity)
    if saved is not None:
        return saved
    return current.place_new_displays(previous or current)


def save_layout(
    layout: Layout, load_layouts: LoadLayoutsPort, save_layouts: SaveLayoutsPort
) -> None:
    layouts = load_layouts()
    layouts[layout.identity] = layout
    save_layouts(layouts)
