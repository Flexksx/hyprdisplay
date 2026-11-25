# hyprdisplay

Display management for Hyprland, starting with a CLI and a background daemon.

The intended workflow is to configure each monitor once and restore its settings when it reconnects.
Settings include resolution, refresh rate, position, scale, and rotation. A graphical interface can come later.

The daemon app models display settings and can load connected Hyprland monitors. The CLI and daemon do not yet
configure displays or save and restore settings.

The root Python workspace contains both apps and uses one `uv.lock` and `.venv`.
Enter the development shell with `nix develop`, then use `just` to list tasks.
Run `uv sync --all-packages` to prepare the shared environment for Zed. Open the
repository root in Zed to use ty, Ruff, and the shared environment.
