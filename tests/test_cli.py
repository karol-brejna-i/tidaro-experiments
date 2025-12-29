"""
Tests for CLI commands (tictl.py)
"""
from unittest.mock import patch, MagicMock
import pytest
from click.testing import CliRunner

from tictl import cli, get_exit_code


@pytest.fixture
def cli_runner():
    """Create a Click test runner."""
    return CliRunner()


@pytest.fixture
def mock_login():
    """Mock the login process to avoid actual API calls."""
    with patch("tictl.get_logged_session") as mock:
        mock.return_value = MagicMock()
        yield mock


class TestCliGroup:
    """Tests for the main CLI group."""

    def test_help_shows_all_commands(self, cli_runner, mock_env_vars):
        result = cli_runner.invoke(cli, ["--help"])
        
        assert result.exit_code == 0
        assert "book-spot" in result.output
        assert "release-spot" in result.output
        assert "show-bookings" in result.output
        assert "show-spots" in result.output
        assert "book-free" in result.output

    def test_exits_on_missing_env(self, cli_runner, clean_env):
        result = cli_runner.invoke(cli, ["show-bookings"])
        
        assert result.exit_code != 0
        assert "Missing environment variable" in result.output or "Error" in result.output


class TestBookSpotCommand:
    """Tests for book-spot command."""

    def test_help_shows_options(self, cli_runner, mock_env_vars):
        result = cli_runner.invoke(cli, ["book-spot", "--help"])
        
        assert result.exit_code == 0
        assert "--date" in result.output
        assert "--spot" in result.output

    def test_accepts_date_option(self, cli_runner, mock_env_vars, mock_login):
        with patch("tidarator.spots.book_spot.BookSpot") as mock_action:
            mock_action.return_value.do.return_value = {
                "action": "book_spot",
                "request": {},
                "result": {"status": "success", "spot": "07", "zone": "Test", "for_date": "2025-01-15"},
            }
            
            result = cli_runner.invoke(cli, ["book-spot", "--date", "2025-01-15"])
            
            assert result.exit_code == 0

    def test_accepts_multiple_spots(self, cli_runner, mock_env_vars, mock_login):
        with patch("tidarator.spots.book_spot.BookSpot") as mock_action:
            mock_action.return_value.do.return_value = {
                "action": "book_spot",
                "request": {},
                "result": {"status": "success", "spot": "07", "zone": "Test", "for_date": "2025-01-15"},
            }
            
            result = cli_runner.invoke(cli, ["book-spot", "-s", "07", "-s", "06"])
            
            # Verify spots were passed to the action
            call_args = mock_action.call_args
            assert "07" in call_args[0][1]["spot_name"]
            assert "06" in call_args[0][1]["spot_name"]


class TestReleaseSpotCommand:
    """Tests for release-spot command."""

    def test_help_shows_options(self, cli_runner, mock_env_vars):
        result = cli_runner.invoke(cli, ["release-spot", "--help"])
        
        assert result.exit_code == 0
        assert "--date" in result.output

    def test_executes_release(self, cli_runner, mock_env_vars, mock_login):
        with patch("tictl.ReleaseSpot") as mock_action:
            mock_action.return_value.do.return_value = {
                "action": "release_spot",
                "request": {"for_date": "2025-01-15"},
                "result": {"status": "success", "message": "Released"},
            }
            
            result = cli_runner.invoke(cli, ["release-spot", "--date", "2025-01-15"])
            
            assert result.exit_code == 0
            mock_action.return_value.do.assert_called_once()


class TestShowBookingsCommand:
    """Tests for show-bookings command."""

    def test_help_available(self, cli_runner, mock_env_vars):
        result = cli_runner.invoke(cli, ["show-bookings", "--help"])
        
        assert result.exit_code == 0

    def test_executes_show_bookings(self, cli_runner, mock_env_vars, mock_login):
        with patch("tictl.ShowBookings") as mock_action:
            mock_action.return_value.do.return_value = {
                "action": "show_bookings",
                "request": {},
                "result": {
                    "status": "success",
                    "bookings": [
                        {"day": "2025-01-06", "free_spots": 5, "my_booking": None},
                    ],
                    "message": "OK",
                },
            }
            
            result = cli_runner.invoke(cli, ["show-bookings"])
            
            assert result.exit_code == 0
            assert "2025-01-06" in result.output


class TestShowSpotsCommand:
    """Tests for show-spots command."""

    def test_help_shows_date_option(self, cli_runner, mock_env_vars):
        result = cli_runner.invoke(cli, ["show-spots", "--help"])
        
        assert result.exit_code == 0
        assert "--date" in result.output

    def test_executes_show_spots(self, cli_runner, mock_env_vars, mock_login):
        with patch("tidarator.spots.show_state.ShowSpotsState") as mock_action:
            mock_action.return_value.do.return_value = {
                "action": "show_spots",
                "request": {"for_date": "2025-01-06", "zone_name": "Test-Zone-A"},
                "result": {
                    "zone": "Test-Zone-A",
                    "for_date": "2025-01-06",
                    "spots": [{"id": "1", "name": "07", "free": True}],
                    "status": "success",
                },
            }
            
            result = cli_runner.invoke(cli, ["show-spots", "--date", "2025-01-06"])
            
            assert result.exit_code == 0


class TestBookFreeCommand:
    """Tests for book-free command."""

    def test_help_shows_options(self, cli_runner, mock_env_vars):
        result = cli_runner.invoke(cli, ["book-free", "--help"])
        
        assert result.exit_code == 0
        assert "--start-from" in result.output
        assert "--look-ahead" in result.output

    def test_start_from_and_look_ahead_mutually_exclusive(self, cli_runner, mock_env_vars, mock_login):
        with patch("tictl.BookFreeSpots") as mock_action:
            mock_action.return_value.do.return_value = {
                "action": "book_free",
                "request": {},
                "result": [],
            }
            
            result = cli_runner.invoke(
                cli, 
                ["book-free", "--start-from", "2025-01-15", "--look-ahead", "7"]
            )
            
            # Should fail because both options are provided
            assert result.exit_code != 0
            assert "either" in result.output.lower() or "not both" in result.output.lower()

    def test_accepts_start_from(self, cli_runner, mock_env_vars, mock_login):
        with patch("tictl.BookFreeSpots") as mock_action:
            mock_action.return_value.do.return_value = {
                "action": "book_free",
                "request": {"look_from": "2025-01-15", "spot_name": ["07"]},
                "result": [],
            }
            
            result = cli_runner.invoke(cli, ["book-free", "--start-from", "2025-01-15"])
            
            assert result.exit_code == 0


class TestDateValidation:
    """Tests for date option validation."""

    def test_rejects_invalid_date_format(self, cli_runner, mock_env_vars):
        result = cli_runner.invoke(cli, ["book-spot", "--date", "15-01-2025"])
        
        assert result.exit_code != 0

    def test_rejects_invalid_date(self, cli_runner, mock_env_vars):
        result = cli_runner.invoke(cli, ["book-spot", "--date", "2025-13-01"])
        
        assert result.exit_code != 0

    def test_accepts_valid_date(self, cli_runner, mock_env_vars, mock_login):
        with patch("tidarator.spots.book_spot.BookSpot") as mock_action:
            mock_action.return_value.do.return_value = {
                "action": "book_spot",
                "request": {},
                "result": {"status": "success", "spot": "07", "zone": "Test", "for_date": "2025-06-15"},
            }
            
            result = cli_runner.invoke(cli, ["book-spot", "--date", "2025-06-15"])
            
            assert result.exit_code == 0


class TestGetExitCode:
    """Tests for get_exit_code helper function."""

    def test_returns_zero_for_success(self):
        result = {"action": "book_spot", "result": {"status": "success"}}
        assert get_exit_code(result) == 0

    def test_returns_one_for_failure(self):
        result = {"action": "book_spot", "result": {"status": "failure"}}
        assert get_exit_code(result) == 1

    def test_returns_one_for_error(self):
        result = {"action": "book_spot", "result": {"status": "error"}}
        assert get_exit_code(result) == 1

    def test_returns_one_for_missing_status(self):
        result = {"action": "book_spot", "result": {}}
        assert get_exit_code(result) == 1

    def test_returns_one_for_missing_result(self):
        result = {"action": "book_spot"}
        assert get_exit_code(result) == 1

    def test_handles_list_with_success(self):
        """book_free returns a list of booking attempts."""
        result = {
            "action": "book_free",
            "result": [
                {"result": {"status": "failure"}},
                {"result": {"status": "success"}},
            ]
        }
        assert get_exit_code(result) == 0

    def test_handles_list_all_failures(self):
        result = {
            "action": "book_free",
            "result": [
                {"result": {"status": "failure"}},
                {"result": {"status": "failure"}},
            ]
        }
        assert get_exit_code(result) == 1

    def test_handles_empty_list(self):
        """Empty list means no spots to book - not a failure."""
        result = {"action": "book_free", "result": []}
        assert get_exit_code(result) == 0
