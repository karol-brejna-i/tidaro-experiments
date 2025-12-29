"""
Tests for tidarator/spots/zone_manager.py and spot_manager.py
"""
from datetime import datetime
from unittest.mock import MagicMock
import pytest

from tidarator.spots.zone_manager import ZoneCacheManager
from tidarator.spots.spot_manager import SpotCacheManager


class TestZoneCacheManager:
    """Tests for ZoneCacheManager class."""

    def test_init_without_force_fetch(self, mock_session):
        manager = ZoneCacheManager(mock_session, force_fetch=False)
        
        # Should not fetch on init
        mock_session.get_zones.assert_not_called()

    def test_init_with_force_fetch(self, mock_session):
        manager = ZoneCacheManager(mock_session, force_fetch=True)
        
        mock_session.get_zones.assert_called_once()

    def test_get_zones_fetches_once(self, mock_session):
        manager = ZoneCacheManager(mock_session)
        
        # First call should fetch
        result1 = manager.get_zones()
        assert mock_session.get_zones.call_count == 1
        
        # Second call should use cache
        result2 = manager.get_zones()
        assert mock_session.get_zones.call_count == 1
        
        assert result1 == result2

    def test_get_by_name_returns_zone(self, mock_session):
        manager = ZoneCacheManager(mock_session)
        
        zone = manager.get_by_name("Test-Zone-A")
        
        assert zone is not None
        assert zone["name"] == "Test-Zone-A"
        assert zone["id"] == "zone-id-1"

    def test_get_by_name_returns_none_for_unknown(self, mock_session):
        manager = ZoneCacheManager(mock_session)
        
        zone = manager.get_by_name("Nonexistent-Zone")
        
        assert zone is None

    def test_get_by_id_returns_zone(self, mock_session):
        manager = ZoneCacheManager(mock_session)
        
        zone = manager.get_by_id("zone-id-2")
        
        assert zone is not None
        assert zone["name"] == "Test-Zone-B"

    def test_get_by_id_returns_none_for_unknown(self, mock_session):
        manager = ZoneCacheManager(mock_session)
        
        zone = manager.get_by_id("unknown-id")
        
        assert zone is None


class TestSpotCacheManager:
    """Tests for SpotCacheManager class."""

    def test_init(self, mock_session):
        manager = SpotCacheManager(mock_session)
        
        # Should not fetch anything on init
        mock_session.get_spots_map.assert_not_called()

    def test_get_spots_fetches_for_zone(self, mock_session):
        manager = SpotCacheManager(mock_session)
        
        spots = manager.get_spots("zone-id-1")
        
        mock_session.get_spots_map.assert_called_once_with("zone-id-1")
        assert len(spots) == 3

    def test_get_spots_caches_result(self, mock_session):
        manager = SpotCacheManager(mock_session)
        
        spots1 = manager.get_spots("zone-id-1")
        spots2 = manager.get_spots("zone-id-1")
        
        # Should only call API once
        assert mock_session.get_spots_map.call_count == 1
        assert spots1 == spots2

    def test_get_spots_different_zones_not_cached(self, mock_session):
        manager = SpotCacheManager(mock_session)
        
        manager.get_spots("zone-id-1")
        manager.get_spots("zone-id-2")
        
        # Should call API for each zone
        assert mock_session.get_spots_map.call_count == 2

    def test_get_by_name_returns_spot(self, mock_session):
        manager = SpotCacheManager(mock_session)
        
        spot = manager.get_by_name("zone-id-1", "07")
        
        assert spot is not None
        assert spot["name"] == "07"
        assert spot["id"] == "spot-id-07"

    def test_get_by_name_returns_none_for_unknown(self, mock_session):
        manager = SpotCacheManager(mock_session)
        
        spot = manager.get_by_name("zone-id-1", "99")
        
        assert spot is None

    def test_get_by_id_returns_spot(self, mock_session):
        manager = SpotCacheManager(mock_session)
        
        spot = manager.get_by_id("zone-id-1", "spot-id-06")
        
        assert spot is not None
        assert spot["name"] == "06"

    def test_get_spots_state_returns_free_status(self, mock_session):
        manager = SpotCacheManager(mock_session)
        
        states = manager.get_spots_state("zone-id-1", datetime(2025, 1, 6))
        
        assert len(states) == 3
        
        spot_07 = next(s for s in states if s["name"] == "07")
        assert spot_07["free"] is True
        
        spot_05 = next(s for s in states if s["name"] == "05")
        assert spot_05["free"] is False

    def test_get_spots_state_passes_date_to_api(self, mock_session):
        manager = SpotCacheManager(mock_session)
        target_date = datetime(2025, 1, 15)
        
        manager.get_spots_state("zone-id-1", target_date)
        
        mock_session.get_spots_map.assert_called_with("zone-id-1", target_date)
