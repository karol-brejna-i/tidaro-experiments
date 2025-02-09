class ZoneCacheManager:
    def __init__(self, session_object, force_fetch: bool = False):
        """
        Initializes with a session object (that the class will use to fetch zones).
        Optionally force_fetch can be set to True to force a fetch of zones on init.
        """
        self.session_object = session_object
        if force_fetch:
            self.__zones = self.session_object.get_zones()
        else:
            self.__zones = None

    def get_zones(self):
        if not self.__zones:
            self.__zones = self.session_object.get_zones()
        return self.__zones

    def get_by_name(self, name) -> dict:
        """
        Search and return a zone object by its 'name'.
        :param name: The name of the zone to search for.
        :return: The zone object or None if not found.
        """
        return next((zone for zone in self.get_zones() if zone.get("name") == name), None)

    def get_by_id(self, zone_id) -> dict:
        """
        Search and return a zone object by its 'id'.
        :param zone_id: The id of the zone to search for.
        :return: The zone object or None if not found.
        """
        return next((zone for zone in self.get_zones() if zone.get("id") == zone_id), None)
