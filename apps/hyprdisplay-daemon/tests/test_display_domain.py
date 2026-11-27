from dataclasses import replace
from math import inf, nan

import pytest

from hyprdisplay_daemon.display.domain import (
    Display,
    DisplayDimensionSize,
    DisplayIdentity,
    DisplayScale,
    Position,
    RefreshRate,
    Resolution,
)


@pytest.mark.parametrize("identity", [("", "", ""), (" ", "\t", " ")])
def test_display_identity_rejects_empty_values(identity: tuple[str, str, str]) -> None:
    with pytest.raises(ValueError, match="identity must not be empty"):
        DisplayIdentity(*identity)


@pytest.mark.parametrize("identity", [("Acme", "", ""), ("", "Panel", ""), ("", "", "1")])
def test_display_identity_accepts_any_nonempty_component(identity: tuple[str, str, str]) -> None:
    assert DisplayIdentity(*identity)


def test_display_dimensions_reject_negative_values() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        DisplayDimensionSize(-1)
    assert DisplayDimensionSize(0).value == 0


@pytest.mark.parametrize("value", [0, -1, inf, -inf, nan])
@pytest.mark.parametrize("value_type", [RefreshRate, DisplayScale])
def test_rates_and_scales_must_be_finite_and_positive(
    value: float, value_type: type[RefreshRate] | type[DisplayScale]
) -> None:
    with pytest.raises(ValueError, match="finite and positive"):
        value_type(value)


def test_resolution_orders_by_area_then_width() -> None:
    smaller = Resolution(DisplayDimensionSize(1280), DisplayDimensionSize(720))
    portrait = Resolution(DisplayDimensionSize(1080), DisplayDimensionSize(1920))
    landscape = Resolution(DisplayDimensionSize(1920), DisplayDimensionSize(1080))
    assert smaller < portrait < landscape
    assert landscape > portrait > smaller


def test_applying_settings_preserves_display_identity(display: Display) -> None:
    settings = replace(display.settings, position=Position(-100, 200))
    updated = display.apply_settings(settings)
    assert updated.settings == settings
    assert updated.identity == display.identity
    assert updated.available_modes == display.available_modes
    assert display.settings.position == Position(0, 0)


def test_refresh_rate_string_includes_unit() -> None:
    assert str(RefreshRate(60)) == "60Hz"
