# hyprdisplay

Display management for Hyprland, starting with a CLI and a background daemon.

The intended workflow is to configure each monitor once and restore its settings when it reconnects.
Settings include resolution, refresh rate, position, scale, and rotation. A graphical interface can come later.

The domain library models saved settings and matches them to connected monitors. The CLI and daemon do not yet
configure displays or save and restore settings.

Enter the development shell with `nix develop`, then use `just` to list tasks.
