from typing import Protocol

from hyprdisplay_daemon.display.domain import Display


class LoadDisplaysPort(Protocol):
    def __call__(self) -> list[Display]: ...


def get_displays(load_displays: LoadDisplaysPort) -> list[Display]:
    return load_displays()
