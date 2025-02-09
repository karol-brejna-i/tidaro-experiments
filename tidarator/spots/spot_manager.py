from datetime import datetime


class SpotCacheManager:
    """
    Responsible for getting and returning spots for given zone.

    It holds (and caches) spots dictionary (id, name).
    """

    def __init__(self, session_object):
        """
        Initializes with a session object (that the class will use to fetch spots).
        Optionally force_fetch can be set to True to force a fetch of spots on init.
        """
        self.session_object = session_object
        self.__spots = {}

    # Extract unique reserved parking spots
    @staticmethod
    def __extract_unique_parking_spots(data):
        result = []
        for spot in data['mapOrNull']['parkingSpots']:
            result.append({'id': spot['id'], 'name': spot['name']})
        return result

    def __fetch_spots(self, zone_id: str):
        data = self.session_object.get_spots_map(zone_id)
        return self.__extract_unique_parking_spots(data)

    def get_spots(self, zone_id: str):
        """
        Return spots dictionary (id, name) for a given zone.
        """
        if not zone_id in self.__spots:
            self.__spots[zone_id] = self.__fetch_spots(zone_id)
        return self.__spots[zone_id]

    def get_by_id(self, zone_id: str, spot_id: str):
        """
        Search and return a spot object by its 'id'.
        :param zone_id: The id of the zone to search for spots in.
        :param spot_id: The id of the spot to search for.
        :return: The spot object or None if not found.
        """
        return next((spot for spot in self.get_spots(zone_id) if spot.get("id") == spot_id), None)

    def get_by_name(self, zone_id: str, name: str):
        """
        Search and return a spot object by its 'name'.
        :param zone_id: The id of the zone to search for spots in.
        :param name: The name of the spot to search for.
        :return: The spot object or None if not found.
        """
        return next((spot for spot in self.get_spots(zone_id) if spot.get("name") == name), None)

    def get_spots_state(self, zone_id: str, for_date: datetime):
        """
        Return current spots' state for a given zone (free/booked)
        """
        data = self.session_object.get_spots_map(zone_id, for_date)
        return list([
            {'id': spot['id'], 'name': spot['name'], 'free': spot['state'] == 'Free'}
            for spot in data['mapOrNull']['parkingSpots']
        ])
