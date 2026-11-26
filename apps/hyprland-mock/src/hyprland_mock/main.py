import asyncio
import os
import socket
from dataclasses import dataclass
from pathlib import Path

import click
from pydantic import TypeAdapter, ValidationError

from hyprland_mock.protocol import (
    RESPONSE,
    Connect,
    Disconnect,
    Failure,
    Keyword,
    ListenerCount,
    Monitor,
    Monitors,
    Status,
)
from hyprland_mock.server import serve

MONITORS = TypeAdapter(list[Monitor])


@dataclass(frozen=True)
class HyprctlOptions:
    json_output: int


def socket_directory() -> Path:
    return Path(os.environ.get("HYPRLAND_MOCK_DIR", "/tmp/hyprland-mock"))


def request(
    command: Connect | Disconnect | Keyword | Monitors | Status,
) -> str | list[Monitor] | ListenerCount:
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
            connection.connect(str(socket_directory() / "control.sock"))
            connection.sendall((command.model_dump_json() + "\n").encode())
            with connection.makefile(encoding="utf-8") as stream:
                response = RESPONSE.validate_json(stream.readline())
    except (OSError, ValidationError) as error:
        raise click.ClickException(str(error)) from error
    if isinstance(response, Failure):
        raise click.ClickException(response.error)
    return response.result


@click.group()
def main() -> None:
    """Simulate Hyprland monitor events."""


@main.command("serve")
def serve_command() -> None:
    """Start the mock server."""
    try:
        asyncio.run(serve(socket_directory()))
    except OSError as error:
        raise click.ClickException(str(error)) from error


@main.command("monitor-connect")
@click.argument("monitor")
def monitor_connect(monitor: str) -> None:
    """Connect a monitor described by a Hyprland JSON object."""
    try:
        parsed = Monitor.model_validate_json(monitor)
    except ValidationError as error:
        raise click.BadParameter(str(error), param_hint="monitor") from error
    click.echo(request(Connect(monitor=parsed)))


@main.command("monitor-disconnect")
@click.argument("name")
def monitor_disconnect(name: str) -> None:
    """Disconnect a monitor by connector name."""
    click.echo(request(Disconnect(name=name)))


@main.command("monitors")
def monitors_command() -> None:
    """Show the connected monitors."""
    result = request(Monitors())
    if not isinstance(result, list):
        raise click.ClickException("Invalid monitors response")
    click.echo(MONITORS.dump_json(result, by_alias=True, indent=2).decode())


@main.command("status")
def status_command() -> None:
    """Show the number of event listeners."""
    result = request(Status())
    if not isinstance(result, ListenerCount):
        raise click.ClickException("Invalid status response")
    click.echo(result.model_dump_json(indent=2))


@click.group()
@click.option("-j", "json_output", count=True)
@click.pass_context
def hyprctl(context: click.Context, json_output: int) -> None:
    """Implement the hyprctl commands used by the daemon."""
    context.obj = HyprctlOptions(json_output=json_output)


@hyprctl.command("monitors")
@click.pass_obj
def hyprctl_monitors(options: HyprctlOptions) -> None:
    if not options.json_output:
        raise click.ClickException("Only JSON monitor output is supported")
    result = request(Monitors())
    if not isinstance(result, list):
        raise click.ClickException("Invalid monitors response")
    click.echo(MONITORS.dump_json(result, by_alias=True).decode())


@hyprctl.group("keyword")
def keyword() -> None:
    """Apply a monitor keyword."""


@keyword.command("monitor")
@click.argument("value")
def keyword_monitor(value: str) -> None:
    click.echo(request(Keyword(value=value)))
