import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest
from conftest import DisplaySystem, monitor


@pytest.fixture
def home_display_system(mock_system: DisplaySystem, tmp_path: Path) -> Iterator[DisplaySystem]:
    layout_path = tmp_path / "layouts.json"
    shutil.copyfile(Path(__file__).parent / "fixtures/home-layout.json", layout_path)
    mock_system.environment["HYPRDISPLAY_LAYOUT_PATH"] = str(layout_path)
    try:
        mock_system.start_daemon()
        yield mock_system
    finally:
        mock_system.stop_daemon()


@pytest.mark.parametrize("order", [(0, 1), (1, 0)], ids=["hdmi-first", "displayport-first"])
def test_home_monitor_layout_is_restored_after_reconnection(
    home_display_system: DisplaySystem, order: tuple[int, int]
) -> None:
    monitors = (
        monitor("HDMI-A-1", "hdmi").model_copy(
            update={"available_modes": ["2560x1440@143.97Hz"], "refresh_rate": 143.97}
        ),
        monitor("DP-1", "displayport").model_copy(
            update={"available_modes": ["2560x1440@155.00Hz"], "refresh_rate": 155.0}
        ),
    )
    positions = ((0, 0), (1440, 0))
    transforms = (1, 0)

    def matches_saved_layout() -> bool:
        actual = {item.name: item for item in home_display_system.monitors()}
        return len(actual) == 2 and all(
            (actual[item.name].x, actual[item.name].y, actual[item.name].transform)
            == (*position, transform)
            and (actual[item.name].width, actual[item.name].height, actual[item.name].refresh_rate)
            == (2560, 1440, item.refresh_rate)
            for item, position, transform in zip(monitors, positions, transforms, strict=True)
        )

    for index in order:
        home_display_system.connect(monitors[index])
        home_display_system.wait_for(
            lambda name=monitors[index].name: any(
                item.name == name and item.width == 2560 for item in home_display_system.monitors()
            ),
            f"{monitors[index].name} to be configured",
        )
    home_display_system.wait_for(matches_saved_layout, "home layout to be restored")

    for index in reversed(order):
        home_display_system.disconnect(monitors[index].name)
        remaining = order.index(index)
        home_display_system.wait_for(
            lambda count=remaining: len(home_display_system.monitors()) == count,
            f"{monitors[index].name} to disconnect",
        )
    for index in order:
        home_display_system.connect(monitors[index])
        home_display_system.wait_for(
            lambda name=monitors[index].name: any(
                item.name == name and item.width == 2560 for item in home_display_system.monitors()
            ),
            f"{monitors[index].name} to be configured",
        )
    home_display_system.wait_for(
        matches_saved_layout, "home layout to be restored after reconnection"
    )
