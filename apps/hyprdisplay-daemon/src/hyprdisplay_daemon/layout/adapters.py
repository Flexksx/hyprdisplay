from pathlib import Path

from pydantic import TypeAdapter

from hyprdisplay_daemon.display.domain import DisplayIdentity
from hyprdisplay_daemon.layout.domain import Layout


def read_layouts(path: Path) -> dict[frozenset[DisplayIdentity], Layout]:
    if not path.exists():
        return {}
    layouts = TypeAdapter(list[Layout]).validate_json(path.read_bytes())
    return {layout.identity: layout for layout in layouts}


def save_layouts(path: Path, layouts: dict[frozenset[DisplayIdentity], Layout]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_bytes(TypeAdapter(list[Layout]).dump_json(list(layouts.values())))
    temporary.replace(path)
