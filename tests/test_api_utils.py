"""
Tests for tidarator/api/utils.py
"""
from datetime import datetime
import pytest

from tidarator.api.utils import date_to_str, str_to_date, DATE_FORMAT


class TestDateToStr:
    """Tests for date_to_str function."""

    def test_converts_datetime_to_string(self):
        dt = datetime(2025, 1, 15)
        result = date_to_str(dt)
        assert result == "2025-01-15"

    def test_uses_correct_format(self):
        dt = datetime(2025, 12, 31)
        result = date_to_str(dt)
        assert result == "2025-12-31"

    def test_pads_single_digit_month(self):
        dt = datetime(2025, 3, 5)
        result = date_to_str(dt)
        assert result == "2025-03-05"

    def test_ignores_time_component(self):
        dt = datetime(2025, 1, 15, 14, 30, 45)
        result = date_to_str(dt)
        assert result == "2025-01-15"


class TestStrToDate:
    """Tests for str_to_date function."""

    def test_converts_string_to_datetime(self):
        result = str_to_date("2025-01-15")
        assert result == datetime(2025, 1, 15)

    def test_parses_end_of_year(self):
        result = str_to_date("2025-12-31")
        assert result.year == 2025
        assert result.month == 12
        assert result.day == 31

    def test_raises_on_invalid_format(self):
        with pytest.raises(ValueError):
            str_to_date("15-01-2025")  # Wrong order

    def test_raises_on_invalid_date(self):
        with pytest.raises(ValueError):
            str_to_date("2025-13-01")  # Invalid month

    def test_raises_on_empty_string(self):
        with pytest.raises(ValueError):
            str_to_date("")


class TestDateFormatConstant:
    """Tests for DATE_FORMAT constant."""

    def test_format_is_iso_style(self):
        assert DATE_FORMAT == r"%Y-%m-%d"


class TestRoundTrip:
    """Tests for converting back and forth."""

    def test_str_to_date_to_str(self):
        original = "2025-06-15"
        dt = str_to_date(original)
        result = date_to_str(dt)
        assert result == original

    def test_date_to_str_to_date(self):
        original = datetime(2025, 6, 15)
        string = date_to_str(original)
        result = str_to_date(string)
        assert result == original
