import pytest

from hyprdisplay.main import main


def test_help(capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.argv", ["hyprdisplay", "--help"])

    with pytest.raises(SystemExit) as result:
        main()

    assert result.value.code == 0
    assert "Manage Hyprland display profiles" in capsys.readouterr().out
