import importlib
import sys


def test_settings_accepts_gateway_force_plaintext_env(monkeypatch):
    monkeypatch.setenv("GATEWAY_FORCE_PLAINTEXT", "true")
    sys.modules.pop("config", None)

    config = importlib.import_module("config")

    assert config.settings.GATEWAY_FORCE_PLAINTEXT is True
