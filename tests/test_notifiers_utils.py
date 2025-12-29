"""
Tests for tidarator/notifiers/utils.py
"""
from datetime import datetime
import pytest

from tidarator.notifiers.utils import format_results


class TestFormatResultsBookSpot:
    """Tests for format_results with book_spot action."""

    def test_formats_successful_booking(self, sample_book_spot_result):
        result = format_results(sample_book_spot_result)
        
        assert "07" in result  # spot name
        assert "Test-Zone-A" in result  # zone name
        assert "2025-01-06" in result  # date

    def test_formats_failed_booking(self, sample_book_spot_failure):
        result = format_results(sample_book_spot_failure)
        
        assert "Couldn't book" in result
        assert "2025-01-06" in result


class TestFormatResultsReleaseSpot:
    """Tests for format_results with release_spot action."""

    def test_formats_release(self, sample_release_spot_result):
        result = format_results(sample_release_spot_result)
        
        assert "released" in result.lower()
        assert "2025-01-07" in result


class TestFormatResultsShowBookings:
    """Tests for format_results with show_bookings action."""

    def test_formats_bookings_list(self, sample_show_bookings_result):
        result = format_results(sample_show_bookings_result)
        
        assert "2025-01-06" in result
        assert "2025-01-07" in result
        assert "07" in result  # booked spot name

    def test_includes_header(self, sample_show_bookings_result):
        result = format_results(sample_show_bookings_result)
        
        assert "bookings" in result.lower()


class TestFormatResultsShowSpots:
    """Tests for format_results with show_spots action."""

    def test_formats_spots_list(self, sample_show_spots_result):
        result = format_results(sample_show_spots_result)
        
        assert "07" in result
        assert "06" in result
        assert "05" in result
        assert "Test-Zone-A" in result

    def test_shows_free_status(self, sample_show_spots_result):
        result = format_results(sample_show_spots_result)
        
        assert "free" in result.lower()


class TestFormatResultsBookFree:
    """Tests for format_results with book_free action."""

    def test_formats_book_free_with_results(self):
        data = {
            "action": "book_free",
            "request": {
                "zone_name": "Test-Zone-A",
                "spot_name": ["07", "06"],
                "look_from": datetime(2025, 1, 6),
            },
            "result": [
                {
                    "action": "book_spot",
                    "request": {"for_date": "2025-01-06", "spot_name": ["07", "06"]},
                    "result": {"status": "success", "spot": "07"},
                },
                {
                    "action": "book_spot",
                    "request": {"for_date": "2025-01-07", "spot_name": ["07", "06"]},
                    "result": {"status": "failure", "messages": []},
                },
            ],
        }
        
        result = format_results(data)
        
        assert "2025-01-06" in result
        assert "07" in result
        assert "FAILED" in result

    def test_formats_book_free_no_spots_found(self):
        data = {
            "action": "book_free",
            "request": {
                "zone_name": "Test-Zone-A",
                "spot_name": ["07"],
                "look_from": datetime(2025, 1, 6),
            },
            "result": [],
        }
        
        result = format_results(data)
        
        assert "No free spots found" in result


class TestFormatResultsUnknownAction:
    """Tests for format_results with unknown action type."""

    def test_handles_unknown_action(self):
        data = {
            "action": "unknown_action",
            "request": {},
            "result": {},
        }
        
        result = format_results(data)
        
        assert "Unknown action type" in result
        assert "unknown_action" in result
