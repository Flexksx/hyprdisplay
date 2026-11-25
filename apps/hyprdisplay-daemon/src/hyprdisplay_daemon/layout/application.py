from typing import Protocol

from hyprdisplay_daemon.display.application import LoadDisplaysPort
from hyprdisplay_daemon.display.domain import DisplayIdentity, Position
from hyprdisplay_daemon.layout.domain import Layout


class LoadLayoutPort(Protocol):
    def __call__(self, identity: frozenset[DisplayIdentity]) -> Layout | None: ...


class SaveLayoutPort(Protocol):
    def __call__(self, layout: Layout) -> None: ...


def connected_layout(
    load_displays: LoadDisplaysPort, load_layout: LoadLayoutPort, connector: str | None = None
) -> Layout:
    displays = load_displays()
    identities = frozenset(display.identity for display in displays)
    if len(identities) != len(displays):
        raise ValueError("Connected displays have duplicate identities")
    saved = load_layout(identities)
    if saved is not None:
        return Layout(
            tuple(
                display.apply_settings(
                    next(
                        item.settings
                        for item in saved.displays
                        if item.identity == display.identity
                    )
                )
                for display in displays
            )
        )
    if connector is None:
        return Layout(tuple(displays))
    connected = next((display for display in displays if display.connector == connector), None)
    if connected is None:
        raise ValueError(f"Connected display unavailable: {connector}")
    return Layout(tuple(display for display in displays if display.connector != connector)).connect(
        connected
    )


def reposition_display(
    load_displays: LoadDisplaysPort,
    load_layout: LoadLayoutPort,
    save_layout: SaveLayoutPort,
    connector: str,
    position: Position,
) -> Layout:
    layout = connected_layout(load_displays, load_layout)
    display = next((item for item in layout.displays if item.connector == connector), None)
    if display is None:
        raise ValueError(f"Unknown display: {connector}")
    layout = layout.reposition(display.identity, position)
    save_layout(layout)
    return layout
