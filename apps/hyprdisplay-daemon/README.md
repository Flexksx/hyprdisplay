# hyprdisplay-daemon

The daemon loads active monitors through `hyprctl -j monitors` and applies display layouts
through `hyprctl keyword monitor`. It rejects flipped transforms, which the display domain
cannot represent. Command failures and invalid monitor data are raised to the caller.

Run `just start daemon` inside a Hyprland session to listen for monitor connections.
The daemon currently ignores disconnect events and exits if the event socket closes.

Set `HYPRDISPLAY_EVENT_SOCKET` to override the Hyprland event socket and
`HYPRDISPLAY_HYPRCTL` to override the `hyprctl` executable. See
[hyprland-mock](../hyprland-mock/README.md) to run the daemon without Hyprland.

Import Linter checks the domain, application, and adapter boundaries as part of `just lint`.
