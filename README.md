# hyprdisplay

Display management for Hyprland, starting with a CLI and a background daemon.

The intended workflow is to save a display arrangement as a profile and restore it when the same monitors reconnect. Profiles should cover modes, positions, scale, and rotation. A graphical interface can come later.

This repository currently contains the project scaffold only. Profile management and the daemon are not implemented yet.

Enter the development shell with `nix develop`, then use `just` to list tasks.
