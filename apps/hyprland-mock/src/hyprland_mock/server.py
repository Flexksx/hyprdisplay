import asyncio
import re
from pathlib import Path

from pydantic import ValidationError

from hyprland_mock.protocol import (
    COMMAND,
    Command,
    Connect,
    Disconnect,
    Failure,
    Keyword,
    ListenerCount,
    Monitor,
    MonitorKeyword,
    Monitors,
    Status,
    Success,
)

KEYWORD_PATTERN = re.compile(
    r"(?P<name>[^,]+),(?P<width>\d+)x(?P<height>\d+)@(?P<refresh_rate>[\d.]+),"
    r"(?P<x>-?\d+)x(?P<y>-?\d+),(?P<scale>[\d.]+),transform,(?P<transform>\d+)"
)


class Mock:
    def __init__(self) -> None:
        self.monitors: dict[str, Monitor] = {}
        self.listeners: set[asyncio.StreamWriter] = set()

    async def events(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        self.listeners.add(writer)
        try:
            await reader.read()
        finally:
            self.listeners.discard(writer)
            writer.close()
            await writer.wait_closed()

    async def control(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            command = COMMAND.validate_json(await reader.readline())
            response = Success(result=self.execute(command))
        except (ValueError, KeyError, ValidationError) as error:
            response = Failure(error=str(error))
        writer.write((response.model_dump_json(by_alias=True) + "\n").encode())
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    def execute(self, command: Command) -> str | list[Monitor] | ListenerCount:
        match command:
            case Monitors():
                return list(self.monitors.values())
            case Status():
                return ListenerCount(listeners=len(self.listeners))
            case Connect(monitor=monitor):
                if monitor.name in self.monitors:
                    raise ValueError(f"Monitor already connected: {monitor.name}")
                self.monitors[monitor.name] = monitor
                self.emit(f"monitoradded>>{monitor.name}\n")
                return "ok"
            case Disconnect(name=name):
                if name not in self.monitors:
                    raise ValueError(f"Monitor not connected: {name}")
                del self.monitors[name]
                self.emit(f"monitorremoved>>{name}\n")
                return "ok"
            case Keyword(value=value):
                self.apply_keyword(value)
                return "ok"

    def apply_keyword(self, value: str) -> None:
        match = KEYWORD_PATTERN.fullmatch(value)
        if match is None:
            raise ValueError(f"Invalid monitor keyword: {value}")
        settings = MonitorKeyword.model_validate(
            match.groupdict() | {"transform": int(match["transform"])}
        )
        monitor = self.monitors[settings.name]
        updated = monitor.model_dump() | settings.model_dump(exclude={"name"})
        self.monitors[settings.name] = Monitor.model_validate(updated)

    def emit(self, event: str) -> None:
        for listener in self.listeners:
            listener.write(event.encode())


async def serve(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    control_path = directory / "control.sock"
    event_path = directory / "events.sock"
    if control_path.exists() or event_path.exists():
        raise FileExistsError(f"Socket already exists in {directory}")
    mock = Mock()
    control = await asyncio.start_unix_server(mock.control, path=control_path)
    try:
        events = await asyncio.start_unix_server(mock.events, path=event_path)
        try:
            async with control, events:
                await asyncio.gather(control.serve_forever(), events.serve_forever())
        finally:
            event_path.unlink(missing_ok=True)
    finally:
        control_path.unlink(missing_ok=True)
