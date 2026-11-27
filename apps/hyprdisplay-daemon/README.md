# hyprdisplay-daemon

The daemon loads active monitors through `hyprctl -j monitors` and applies display layouts
through `hyprctl keyword monitor`. It rejects flipped transforms, which the display domain
cannot represent. Command failures and invalid monitor data are raised to the caller.

Run `just start daemon` inside a Hyprland session to listen for monitor connections.
On disconnect, the daemon restores the saved layout for the remaining monitors, or keeps
their current positions when no layout is saved. It exits if the event socket closes.

Set `HYPRDISPLAY_EVENT_SOCKET` to override the Hyprland event socket and
`HYPRDISPLAY_HYPRCTL` to override the `hyprctl` executable. Set `HYPRDISPLAY_LAYOUT_PATH`
to choose the layout file. It defaults to `$XDG_CONFIG_HOME/hyprdisplay/layouts.json`,
or `~/.config/hyprdisplay/layouts.json` when `XDG_CONFIG_HOME` is unset. See
[mock-hyprland](../mock-hyprland/README.md) to run the daemon without Hyprland.

Import Linter checks the domain, application, and adapter boundaries as part of `just lint`.
