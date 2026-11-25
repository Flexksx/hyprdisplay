# hyprdisplay-daemon

Run `just start daemon` in a Hyprland session. The daemon checks the
active displays every second. It places a newly connected display to the right
of the existing displays and restores the last saved settings when a known set
of displays returns. Changes made in Hyprland are saved automatically.

A layout is identified by each display's connector, make, model and serial.
By default, layouts are saved in `$XDG_STATE_HOME/hyprdisplay/layouts.json`, or
`~/.local/state/hyprdisplay/layouts.json` when `XDG_STATE_HOME` is unset or empty.
Set `HYPRDISPLAY_LAYOUTS_PATH` to use a different file. Set
`HYPRDISPLAY_POLL_INTERVAL` to change the polling interval in seconds; it must
be greater than zero.
It restores resolution, refresh rate, position, scale and transform. The daemon
requires `hyprctl` and a running Hyprland session.
