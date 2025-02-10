from datetime import datetime, timedelta

from . import utils
from .session_base import ParkanizerSessionBase, PARKANIZER_API
from ..log_config import get_logger

logger = get_logger(__name__)


class ParkanizerSpotSession(ParkanizerSessionBase):
    """
    ParkanizerSpotSession is a specialized class for managing parking spot reservations
    using the Parkanizer API.

    It allows to authenticate a user and interact with the Parkanizer API endpoints while maintaining
    session state.


    This class provides methods for:
    - Fetching available parking zones (`get_zones`)
    - Retrieving the user's active reservations (`get_my_reservations`)
    - Reserving a parking spot for a specific date (`take_spot`)
    - Releasing or sharing a parking spot reservation (`release_spot`)
    - Getting a list of employees who can benefit from a cancelled reservation (`get_beneficiares`)

    The implemented methods interact with various endpoints of the Parkanizer API to manage
    parking-related tasks effectively.
    """

    def __init__(self):
        super().__init__()
        # marketplace/get-parking-spot-zones
        self.GET_EMPLOYEES_URL = PARKANIZER_API + "/employee-reservations/get-employees"
        self.GET_ZONES_URL = PARKANIZER_API + "/marketplace/get-parking-spot-zones"
        self.GET_MY_RESERVATIONS_URL = PARKANIZER_API + "/employee-reservations/get-employee-reservations"
        self.TAKE_SPOT_URL = PARKANIZER_API + "/employee-reservations/take-spot-from-marketplace"
        self.RELEASE_SPOT_URL = PARKANIZER_API + "/employee-reservations/resign"
        self.GET_SPOTS_URL = PARKANIZER_API + "/marketplace/get-spots"
        self.GET_SPOTS_MAP_URL = PARKANIZER_API + "/marketplace/get-marketplace-parking-spot-zone-map"

    def get_zones(self) -> list[dict[str, str]]:
        return self._post(self.GET_ZONES_URL)["parkingSpotZones"]

    def get_my_reservations(self):
        return self._get(self.GET_MY_RESERVATIONS_URL)["reservations"]

    def get_spots(self, zone_id: str):
        """
        This method uses reserved/available spots endpoint.
        It gets spots from a perspective of today
        (in the service, there is the matter of an active reservation windows: from today until next x-days).
        """
        # post z {
        #   "parkingSpotZoneId":"d74b0000-bd9a-6045-2d7e-08dcac99dcf8",
        #   "bookingTimeInterval":{"fromBookingTime":"P0DT00H00M","toBookingTime":"P1DT00H00M"}
        #   }
        payload = {
            "parkingSpotZoneId": zone_id,
            "bookingTimeInterval": {"fromBookingTime": "P0DT00H00M", "toBookingTime": "P1DT00H00M"}
        }

        return self._post(self.GET_SPOTS_URL, payload)

    def get_spots_map(self, zone_id: str, for_date: datetime = None):
        """
        This method lists spots for a given zone.
        """
        # {
        # "parkingSpotZoneId":"d74b0000-bd9a-6045-89d6-08daf2832b43",
        # "date":"2025-02-15",
        # "bookingTimeInterval":{"fromBookingTime":"P0DT00H00M","toBookingTime":"P1DT00H00M"}
        # }
        if for_date is None:
            for_date = datetime.today()
        payload = {
            "parkingSpotZoneId": zone_id,
            "date": utils.date_to_str(for_date),
            "bookingTimeInterval": {"fromBookingTime": "P0DT00H00M", "toBookingTime": "P1DT00H00M"}
        }

        return self._post(self.GET_SPOTS_MAP_URL, payload)

    def take_spot(self, zone_id: str, spot_id: str, day: datetime | str):
        logger.info(f'Taking Spot {spot_id} for {day} (in {zone_id})')
        # if day is instance of datetime, convert to string:
        if type(day) is datetime:
            day = utils.date_to_str(day)
        payload = {
            "dayToTake": day,
            "parkingSpotZoneId": zone_id,
            "parkingSpotIdOrNull": spot_id,
            "bookingTimeInterval": {"fromBookingTime": "P0DT00H00M", "toBookingTime": "P1DT00H00M"}
        }
        # if no spot_id is provided, parkanizer will try to book any spot available (the payload then does not include parkingSpotIdOrNull field
        if not spot_id:
            del payload['parkingSpotIdOrNull']
        return self._post(self.TAKE_SPOT_URL, payload)

    def release_spot(self, day: datetime | str):

        if type(day) is datetime:
            day = utils.date_to_str(day)

        payload = {"daysToShare": [day], "receivingEmployeeIdOrNull": None}
        return self._post(self.RELEASE_SPOT_URL, payload)

    def get_beneficiares(self, for_date: datetime) -> list[dict[str, str]]:
        """
        This method returns employees that can receive cancelled reservation.
        """
        logger.info('get beneficiaries')

        days_to_share = utils.date_to_str(for_date + timedelta(days=1))
        payload = {"daysToShare": [days_to_share]}
        logger.debug(payload)
        return self._post(self.GET_EMPLOYEES_URL, payload)["employeesOrNull"]
