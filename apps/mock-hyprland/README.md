# mock-hyprland

Simulate monitor connections without a Hyprland session. The mock keeps monitor state in
memory and implements the `hyprctl` commands used by the daemon.

Start the mock in one terminal:

```sh
export MOCK_HYPRLAND_DIR=/tmp/mock-hyprland
cd apps/mock-hyprland
uv run mock-hyprland serve
```

In another terminal, configure and start the daemon. Use the same mock directory in every
terminal. Isolate the daemon's saved layouts if you do not want to use your normal layouts.

```sh
export MOCK_HYPRLAND_DIR=/tmp/mock-hyprland
export HYPRDISPLAY_EVENT_SOCKET=$MOCK_HYPRLAND_DIR/events.sock
export HYPRDISPLAY_HYPRCTL="$PWD/apps/mock-hyprland/.venv/bin/mock-hyprland-hyprctl"
export XDG_CONFIG_HOME=/tmp/hyprdisplay-mock-config
just start daemon
```

Wait until `uv run --project apps/mock-hyprland mock-hyprland status` reports a listener,
then send a monitor object using the fields returned by `hyprctl -j monitors`:

```sh
uv run --project apps/mock-hyprland mock-hyprland monitor-connect '{"name":"DP-1","availableModes":["1920x1080@60.00Hz"],"make":"Acme","model":"Panel","serial":"1","width":1920,"height":1080,"refreshRate":60.0,"x":0,"y":0,"scale":1.0,"transform":0}'
uv run --project apps/mock-hyprland mock-hyprland monitors
uv run --project apps/mock-hyprland mock-hyprland monitor-disconnect DP-1
```

`monitors` shows the state after the daemon applies its layout. Disconnect events are emitted,
but the daemon currently handles only connection events. Stop both processes with Ctrl+C.
If the mock is killed without cleanup, remove its socket files before starting it again.
