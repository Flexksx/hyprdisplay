import json
import os
from pathlib import Path

from pydantic import TypeAdapter

from hyprdisplay_daemon.display.domain import DisplayIdentity
from hyprdisplay_daemon.layout.domain import Layout


def layout_path() -> Path:
    return (
        Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        / "hyprdisplay"
        / "layouts.json"
    )


def load_layouts() -> list[Layout]:
    path = layout_path()
    if not path.exists():
        return []
    return TypeAdapter(list[Layout]).validate_json(path.read_text())


def load_layout(identity: frozenset[DisplayIdentity]) -> Layout | None:
    return next((layout for layout in load_layouts() if layout.identity == identity), None)


def save_layout(layout: Layout) -> None:
    layouts = [item for item in load_layouts() if item.identity != layout.identity]
    layouts.append(layout)
    path = layout_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(TypeAdapter(list[Layout]).dump_python(layouts, mode="json"), indent=2)
    )
    temporary.replace(path)
