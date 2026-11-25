from dataclasses import dataclass, replace

from hyprdisplay_daemon.display.domain import Display, DisplayIdentity, Position


@dataclass(frozen=True, slots=True)
class Layout:
    displays: tuple[Display, ...]

    def __post_init__(self) -> None:
        identities = [display.identity for display in self.displays]
        if len(set(identities)) != len(identities):
            raise ValueError("Layout contains duplicate display identities")

    @property
    def identity(self) -> frozenset[DisplayIdentity]:
        return frozenset(display.identity for display in self.displays)

    def place_new_displays(self, previous: Layout) -> Layout:
        existing = [display for display in self.displays if display.identity in previous.identity]
        new = [display for display in self.displays if display.identity not in previous.identity]
        if not existing and new:
            existing.append(new.pop(0))
        for display in new:
            right = max(
                item.settings.position.x
                + round(item.settings.mode.width.value / item.settings.scale.value)
                for item in existing
            )
            position = Position(x=right, y=min(item.settings.position.y for item in existing))
            existing.append(display.apply_settings(replace(display.settings, position=position)))
        return Layout(tuple(existing))
