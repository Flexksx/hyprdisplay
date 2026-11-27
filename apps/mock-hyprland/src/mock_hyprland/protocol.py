from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter


class Monitor(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True, strict=True)

    name: str = Field(min_length=1, pattern=r"^[^,\n]+$")
    available_modes: list[str] = Field(alias="availableModes")
    make: str
    model: str
    serial: str
    width: int
    height: int
    refresh_rate: float = Field(alias="refreshRate")
    x: int
    y: int
    scale: float
    transform: Literal[0, 1, 2, 3]


class Connect(BaseModel):
    action: Literal["connect"] = "connect"
    monitor: Monitor


class Disconnect(BaseModel):
    action: Literal["disconnect"] = "disconnect"
    name: str


class Monitors(BaseModel):
    action: Literal["monitors"] = "monitors"


class Status(BaseModel):
    action: Literal["status"] = "status"


class Keyword(BaseModel):
    action: Literal["keyword"] = "keyword"
    value: str


Command = Annotated[
    Connect | Disconnect | Monitors | Status | Keyword, Field(discriminator="action")
]
COMMAND = TypeAdapter(Command)


class ListenerCount(BaseModel):
    listeners: int


class Success(BaseModel):
    status: Literal["ok"] = "ok"
    result: str | list[Monitor] | ListenerCount


class Failure(BaseModel):
    status: Literal["error"] = "error"
    error: str


Response = Annotated[Success | Failure, Field(discriminator="status")]
RESPONSE = TypeAdapter(Response)


class MonitorKeyword(BaseModel):
    name: str
    width: int
    height: int
    refresh_rate: float
    x: int
    y: int
    scale: float
    transform: Literal[0, 1, 2, 3]
