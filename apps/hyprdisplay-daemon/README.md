# hyprdisplay-daemon

The display module models displays and loads active Hyprland monitors:

```python
from hyprdisplay_daemon.display import get_displays
from hyprdisplay_daemon.display.adapters import load_displays

displays = get_displays(load_displays)
```

The adapter runs `hyprctl -j monitors`. It requires a running Hyprland session and
rejects flipped transforms, which the display domain cannot represent. Command
failures and invalid monitor data are raised to the caller.

Import Linter checks the domain, application, and adapter boundaries as part of
`just lint`. Run `just start daemon` inside a Hyprland session to listen for monitor
connections and disconnections. For each connection, it logs the monitor's complete
Hyprland JSON configuration. For each disconnection, it logs the monitor name. Stop it with Ctrl+C. The process exits if the event socket closes.
