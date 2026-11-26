# hyprdisplay

Display management for Hyprland, starting with a CLI and a background daemon.

The intended workflow is to configure each monitor once and restore its settings when it reconnects.
Settings include resolution, refresh rate, position, scale, and rotation. A graphical interface can come later.

The daemon configures connected monitors and can save and restore layouts. The separate CLI does not yet
communicate with the daemon.

Enter the development shell with `nix develop`, then use `just` to list tasks.

Run `just sync` to create the task indexes, then `just test repo` for the project-level
tests. They start the daemon and mock in separate processes with isolated sockets and
configuration. `just test all` includes these tests along with the app tests.
