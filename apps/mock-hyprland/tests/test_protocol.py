import pytest
from pydantic import ValidationError

from mock_hyprland.protocol import COMMAND


def test_connect_rejects_incomplete_monitor() -> None:
    with pytest.raises(ValidationError, match="availableModes"):
        COMMAND.validate_json('{"action":"connect","monitor":{"name":"DP-1"}}')
