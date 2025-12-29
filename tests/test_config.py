"""
Tests for tidarator/config.py
"""
import os
import pathlib
import pytest

from tidarator.config import (
    MissingEnvironmentVariableError,
    get_env_or_crash,
    get_path_or_default,
    parse_notifiers,
    load_config,
)


class TestMissingEnvironmentVariableError:
    """Tests for the custom exception class."""

    def test_error_message_contains_env_name(self):
        error = MissingEnvironmentVariableError("TEST_VAR")
        assert "TEST_VAR" in str(error)
        assert error.env_name == "TEST_VAR"

    def test_error_is_exception(self):
        error = MissingEnvironmentVariableError("TEST_VAR")
        assert isinstance(error, Exception)


class TestGetEnvOrCrash:
    """Tests for get_env_or_crash function."""

    def test_returns_value_when_set(self, monkeypatch):
        monkeypatch.setenv("TEST_VAR", "test_value")
        result = get_env_or_crash("TEST_VAR")
        assert result == "test_value"

    def test_raises_when_not_set(self, clean_env):
        with pytest.raises(MissingEnvironmentVariableError) as exc_info:
            get_env_or_crash("NONEXISTENT_VAR")
        assert exc_info.value.env_name == "NONEXISTENT_VAR"

    def test_raises_when_empty_string(self, monkeypatch):
        monkeypatch.setenv("EMPTY_VAR", "")
        with pytest.raises(MissingEnvironmentVariableError):
            get_env_or_crash("EMPTY_VAR")


class TestGetPathOrDefault:
    """Tests for get_path_or_default function."""

    def test_returns_path_when_set(self, monkeypatch):
        monkeypatch.setenv("PATH_VAR", "/tmp/test/path")
        result = get_path_or_default("PATH_VAR")
        assert isinstance(result, pathlib.Path)
        assert str(result) == "/tmp/test/path"

    def test_returns_default_when_not_set(self, clean_env):
        default = pathlib.Path("/default/path")
        result = get_path_or_default("NONEXISTENT_PATH", default)
        assert result == default

    def test_returns_none_when_not_set_and_no_default(self, clean_env):
        result = get_path_or_default("NONEXISTENT_PATH")
        assert result is None

    def test_resolves_relative_path(self, monkeypatch):
        monkeypatch.setenv("PATH_VAR", "./relative/path")
        result = get_path_or_default("PATH_VAR")
        assert result.is_absolute()


class TestParseNotifiers:
    """Tests for parse_notifiers function."""

    def test_parses_gmail_notifier(self, monkeypatch, clean_env):
        monkeypatch.setenv("NOTIFIERS_GMAIL_USER", "sender@gmail.com")
        monkeypatch.setenv("NOTIFIERS_GMAIL_PASSWORD", "secret123")
        monkeypatch.setenv("NOTIFIERS_GMAIL_RECIPIENT", "recipient@example.com")
        
        result = parse_notifiers()
        
        assert "gmail" in result
        assert result["gmail"]["user"] == "sender@gmail.com"
        assert result["gmail"]["password"] == "secret123"
        assert result["gmail"]["recipient"] == "recipient@example.com"

    def test_returns_empty_dict_when_no_notifiers(self, clean_env):
        result = parse_notifiers()
        assert result == {}

    def test_handles_multiple_notifier_types(self, monkeypatch, clean_env):
        monkeypatch.setenv("NOTIFIERS_GMAIL_USER", "gmail@test.com")
        monkeypatch.setenv("NOTIFIERS_SLACK_WEBHOOK", "https://hooks.slack.com/xxx")
        
        result = parse_notifiers()
        
        assert "gmail" in result
        assert "slack" in result
        assert result["gmail"]["user"] == "gmail@test.com"
        assert result["slack"]["webhook"] == "https://hooks.slack.com/xxx"

    def test_notifier_type_is_lowercase(self, monkeypatch, clean_env):
        monkeypatch.setenv("NOTIFIERS_GMAIL_USER", "test@test.com")
        
        result = parse_notifiers()
        
        assert "gmail" in result
        assert "GMAIL" not in result


class TestLoadConfig:
    """Tests for load_config function."""

    def test_loads_minimal_config(self, mock_env_vars):
        config = load_config()
        
        assert config["tidaro"]["user"] == "test@example.com"
        assert config["tidaro"]["password"] == "testpassword"
        assert config["book-spot"]["zone"] == "Test-Zone-A"
        assert config["book-spot"]["spots"] == ["07", "06", "*"]

    def test_raises_when_user_missing(self, monkeypatch, clean_env):
        monkeypatch.setenv("TIDARO_PASSWORD", "pass")
        monkeypatch.setenv("SPOT_ZONE", "zone")
        monkeypatch.setenv("SPOT_NAMES", "07")
        
        with pytest.raises(MissingEnvironmentVariableError) as exc_info:
            load_config()
        assert exc_info.value.env_name == "TIDARO_USER"

    def test_raises_when_password_missing(self, monkeypatch, clean_env):
        monkeypatch.setenv("TIDARO_USER", "user@test.com")
        monkeypatch.setenv("SPOT_ZONE", "zone")
        monkeypatch.setenv("SPOT_NAMES", "07")
        
        with pytest.raises(MissingEnvironmentVariableError) as exc_info:
            load_config()
        assert exc_info.value.env_name == "TIDARO_PASSWORD"

    def test_raises_when_zone_missing(self, monkeypatch, clean_env):
        monkeypatch.setenv("TIDARO_USER", "user@test.com")
        monkeypatch.setenv("TIDARO_PASSWORD", "pass")
        monkeypatch.setenv("SPOT_NAMES", "07")
        
        with pytest.raises(MissingEnvironmentVariableError) as exc_info:
            load_config()
        assert exc_info.value.env_name == "SPOT_ZONE"

    def test_raises_when_spot_names_missing(self, monkeypatch, clean_env):
        monkeypatch.setenv("TIDARO_USER", "user@test.com")
        monkeypatch.setenv("TIDARO_PASSWORD", "pass")
        monkeypatch.setenv("SPOT_ZONE", "zone")
        
        with pytest.raises(MissingEnvironmentVariableError) as exc_info:
            load_config()
        assert exc_info.value.env_name == "SPOT_NAMES"

    def test_parses_spot_names_comma_separated(self, monkeypatch, clean_env):
        monkeypatch.setenv("TIDARO_USER", "user@test.com")
        monkeypatch.setenv("TIDARO_PASSWORD", "pass")
        monkeypatch.setenv("SPOT_ZONE", "zone")
        monkeypatch.setenv("SPOT_NAMES", "25, 08, *")
        
        config = load_config()
        
        assert config["book-spot"]["spots"] == ["25", "08", "*"]

    def test_strips_quotes_from_spot_names(self, monkeypatch, clean_env):
        monkeypatch.setenv("TIDARO_USER", "user@test.com")
        monkeypatch.setenv("TIDARO_PASSWORD", "pass")
        monkeypatch.setenv("SPOT_ZONE", "zone")
        monkeypatch.setenv("SPOT_NAMES", "'25','08','*'")
        
        config = load_config()
        
        assert config["book-spot"]["spots"] == ["25", "08", "*"]

    def test_default_look_ahead_is_zero(self, mock_env_vars, monkeypatch):
        # Explicitly unset LOOK_AHEAD to test default
        monkeypatch.delenv("LOOK_AHEAD", raising=False)
        
        config = load_config()
        
        assert config["check-spots"]["look-ahead"] == 0

    def test_respects_look_ahead_env(self, mock_env_vars, monkeypatch):
        monkeypatch.setenv("LOOK_AHEAD", "7")
        
        config = load_config()
        
        assert config["check-spots"]["look-ahead"] == 7

    def test_includes_notifiers_when_configured(self, mock_env_with_notifiers):
        config = load_config()
        
        assert "gmail" in config["notifiers"]
        assert config["notifiers"]["gmail"]["user"] == "sender@gmail.com"

    def test_notifiers_empty_when_not_configured(self, mock_env_vars, monkeypatch):
        # Explicitly clear any notifier env vars
        for key in list(os.environ.keys()):
            if key.startswith("NOTIFIERS_"):
                monkeypatch.delenv(key, raising=False)
        
        config = load_config()
        
        assert config["notifiers"] == {}
