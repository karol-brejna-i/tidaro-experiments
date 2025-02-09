class BookingsCacheManager:
    """
    Responsible for getting and user's bookings for given zone.
    Keeps a short-live cache of bookings.
    """

    # Extract unique reserved parking spots
    @staticmethod
    def __list_days(data):
        for week in data.get("weeks", []):
            for day_entry in week.get("week", []):
                day = day_entry.get("day")
                free_spots = day_entry.get("freeSpots")
                my_booking = {}
                reserved_spot = day_entry.get("reservedParkingSpotOrNull")
                if reserved_spot:
                    my_booking = {
                        "id": reserved_spot["id"],
                        "name": reserved_spot["name"],
                        "parkingSpotZoneId": reserved_spot["parkingSpotZoneId"],
                        "parkingSpotZoneName": reserved_spot["parkingSpotZoneName"]
                    }
                yield {'day': day, 'free_spots': free_spots, 'my_booking': my_booking}

    def __fetch_spots(self, zone_id: str):
        data = self.session_object.get_spots(zone_id)
        return sorted(self.__list_days(data), key=lambda x: x['day'])

    def __init__(self, session_object):
        """
        Initializes with a session object (that the class will use to fetch spots).
        Optionally force_fetch can be set to True to force a fetch of spots on init.
        """
        self.session_object = session_object
        self.__bookings = {}

    def get_bookings(self, zone_id: str):
        if not zone_id in self.__bookings:
            self.__bookings[zone_id] = self.__fetch_spots(zone_id)
        return self.__bookings[zone_id]

    def get_by_date(self, zone_id: str, day: str):
        """
        Search and return a spot object by its 'id'.
        :param zone_id: The id of the zone to search for spots in.
        :param day: The day of the reservation
        :return: The spot object or None if not found.
        """
        return next((spot for spot in self.get_bookings(zone_id) if spot.get("day") == day), None)
