from typing import Protocol

from hyprdisplay_daemon.display.domain import Display


class LoadDisplaysPort(Protocol):
    def __call__(self) -> list[Display]: ...


class ApplyDisplayPort(Protocol):
    def __call__(self, display: Display) -> None: ...


def get_displays(load_displays: LoadDisplaysPort) -> list[Display]:
    return load_displays()


def apply_displays(
    current: tuple[Display, ...], target: tuple[Display, ...], apply_display: ApplyDisplayPort
) -> bool:
    current_displays = {display.identity: display for display in current}
    changed = False
    for display in target:
        if display != current_displays[display.identity]:
            apply_display(display)
            changed = True
    return changed
