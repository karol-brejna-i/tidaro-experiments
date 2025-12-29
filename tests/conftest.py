"""
Pytest configuration and shared fixtures for tidarator tests.
"""
import os
import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up required environment variables for testing."""
    env_vars = {
        "TIDARO_USER": "test@example.com",
        "TIDARO_PASSWORD": "testpassword",
        "SPOT_ZONE": "Test-Zone-A",
        "SPOT_NAMES": "07,06,*",
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    return env_vars


@pytest.fixture
def mock_env_with_notifiers(mock_env_vars, monkeypatch):
    """Environment variables including Gmail notifier config."""
    notifier_vars = {
        "NOTIFIERS_GMAIL_USER": "sender@gmail.com",
        "NOTIFIERS_GMAIL_PASSWORD": "app-password",
        "NOTIFIERS_GMAIL_RECIPIENT": "recipient@example.com",
    }
    for key, value in notifier_vars.items():
        monkeypatch.setenv(key, value)
    return {**mock_env_vars, **notifier_vars}


@pytest.fixture
def clean_env(monkeypatch):
    """Remove all tidarator-related environment variables."""
    keys_to_remove = [
        "TIDARO_USER",
        "TIDARO_PASSWORD", 
        "SPOT_ZONE",
        "SPOT_NAMES",
        "LOOK_AHEAD",
        "NOTIFIERS_GMAIL_USER",
        "NOTIFIERS_GMAIL_PASSWORD",
        "NOTIFIERS_GMAIL_RECIPIENT",
        "SESSION_SECRETS_DIR",
        "LOGGING_CONFIG_PATH",
        "LOG_DIR",
        "LOG_LEVEL",
    ]
    for key in keys_to_remove:
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
def mock_session():
    """Create a mock session object that simulates ParkanizerSpotSession."""
    session = MagicMock()
    
    # Mock get_zones response
    session.get_zones.return_value = [
        {"id": "zone-id-1", "name": "Test-Zone-A"},
        {"id": "zone-id-2", "name": "Test-Zone-B"},
    ]
    
    # Mock get_my_reservations response
    session.get_my_reservations.return_value = []
    
    # Mock get_spots_map response
    session.get_spots_map.return_value = {
        "mapOrNull": {
            "parkingSpots": [
                {"id": "spot-id-07", "name": "07", "state": "Free"},
                {"id": "spot-id-06", "name": "06", "state": "Free"},
                {"id": "spot-id-05", "name": "05", "state": "Reserved"},
            ]
        }
    }
    
    # Mock take_spot response (successful booking)
    session.take_spot.return_value = {
        "status": "Reserved",
        "receivedParkingSpotOrNull": {
            "id": "spot-id-07",
            "name": "07",
            "parkingSpotZoneId": "zone-id-1",
            "parkingSpotZoneName": "Test-Zone-A",
        }
    }
    
    # Mock release_spot response
    session.release_spot.return_value = {}
    
    # Mock get_spots response (for bookings)
    session.get_spots.return_value = {
        "weeks": [
            {
                "week": [
                    {
                        "day": "2025-01-06",
                        "freeSpots": 5,
                        "reservedParkingSpotOrNull": None,
                    },
                    {
                        "day": "2025-01-07",
                        "freeSpots": 3,
                        "reservedParkingSpotOrNull": {
                            "id": "spot-id-07",
                            "name": "07",
                            "parkingSpotZoneId": "zone-id-1",
                            "parkingSpotZoneName": "Test-Zone-A",
                        },
                    },
                ]
            }
        ]
    }
    
    return session


@pytest.fixture
def sample_book_spot_result():
    """Sample successful book_spot result data."""
    return {
        "action": "book_spot",
        "request": {
            "for_date": "2025-01-06",
            "zone_name": "Test-Zone-A",
            "spot_name": ["07", "06"],
        },
        "result": {
            "zone": "Test-Zone-A",
            "spot": "07",
            "for_date": "2025-01-06",
            "status": "success",
        },
    }


@pytest.fixture
def sample_book_spot_failure():
    """Sample failed book_spot result data."""
    return {
        "action": "book_spot",
        "request": {
            "for_date": "2025-01-06",
            "zone_name": "Test-Zone-A",
            "spot_name": ["07"],
        },
        "result": {
            "status": "failure",
            "messages": ["Couldn't reserve spot spot-id-07 for 2025-01-06"],
        },
    }


@pytest.fixture
def sample_show_bookings_result():
    """Sample show_bookings result data."""
    return {
        "action": "show_bookings",
        "request": {"zone_name": "Test-Zone-A"},
        "result": {
            "status": "success",
            "bookings": [
                {"day": "2025-01-06", "free_spots": 5, "my_booking": None},
                {
                    "day": "2025-01-07",
                    "free_spots": 3,
                    "my_booking": {"id": "spot-id-07", "name": "07"},
                },
            ],
            "message": "Retrieved booking info successfully",
        },
    }


@pytest.fixture  
def sample_release_spot_result():
    """Sample release_spot result data."""
    return {
        "action": "release_spot",
        "request": {"for_date": "2025-01-07"},
        "result": {
            "status": "success",
            "message": "Released spot for 2025-01-07 successfully",
        },
    }


@pytest.fixture
def sample_show_spots_result():
    """Sample show_spots result data."""
    return {
        "action": "show_spots",
        "request": {"for_date": "2025-01-06", "zone_name": "Test-Zone-A"},
        "result": {
            "zone": "Test-Zone-A",
            "for_date": "2025-01-06",
            "spots": [
                {"id": "spot-id-07", "name": "07", "free": True},
                {"id": "spot-id-06", "name": "06", "free": True},
                {"id": "spot-id-05", "name": "05", "free": False},
            ],
            "status": "success",
        },
    }
