import io
from datetime import datetime, timedelta

from . import utils
from .session_base import ParkanizerSessionBase, PARKANIZER_API
from ..log_config import get_logger

logger = get_logger(__name__)


class ParkanizerDeskSession(ParkanizerSessionBase):
    def __init__(self):
        super().__init__()
        self.GET_ZONES_URL = PARKANIZER_API + "/employee-desks/desk-marketplace/get-marketplace-zones"
        self.GET_EMPLOYEES_URL = PARKANIZER_API + "/employee-reservations/get-employees"
        self.GET_DESK_ZONE_MAP_URL = PARKANIZER_API + "/employee-desks/desk-marketplace/get-marketplace-desk-zone-map"
        self.GET_AVAILABLE_DAYS_URL = PARKANIZER_API + "/employee-desks/desk-marketplace/get-marketplace-desks"
        self.GET_EMPLOYEE_RESERVATIONS_URL = PARKANIZER_API + "/employee-desks/colleague-finder/get-colleague-desk-reservations"
        self.TAKE_DESK_URL = PARKANIZER_API + "/employee-desks/desk-marketplace/take"
        self.RELEASE_DESK_URL = PARKANIZER_API + "/employee-desks/share-desk/free"
        self.GET_ZONE_IMAGE_URL = PARKANIZER_API + "/components/desk-zone-map/desk-zone-map-image/"
        self.GET_MY_RESERVATIONS_URL = PARKANIZER_API + "/employee-desks/my-desk/initialize-my-desk-view"
        self.SEARCH_COLLEAGUE_URL = PARKANIZER_API + "/employee-desks/colleague-finder/search"

    def get_zones(self) -> list[dict[str, str]]:
        return self._post(self.GET_ZONES_URL)["zones"]

    def get_employees(self) -> list[dict[str, str]]:
        days_to_share = utils.date_to_str(datetime.today() + timedelta(days=32))
        payload = {"daysToShare": [days_to_share]}
        return self._post(self.GET_EMPLOYEES_URL, payload)["employeesOrNull"]

    def get_desk_zone_map(self, zone_id: str, date: datetime = datetime.today()) -> list[dict[str, str]]:
        payload = {"date": utils.date_to_str(date), "deskZoneId": zone_id}
        return self._post(self.GET_DESK_ZONE_MAP_URL, payload)["mapOrNull"]["desks"]

    def get_available_days(self, zone_id: str) -> list[datetime]:
        payload = {"zoneId": zone_id}
        return [
            utils.str_to_date(day["day"])
            for week in self._post(self.GET_AVAILABLE_DAYS_URL, payload)["weeks"]
            for day in week["week"]
        ]

    def get_employee_reservations(self, employee_id: str) -> list[dict[str, str]]:
        payload = {"colleagueId": employee_id}
        return self._post(self.GET_EMPLOYEE_RESERVATIONS_URL, payload)["deskReservations"]

    def take_desk(self, zone_id: str, desk_id: str, day: datetime):
        payload = {
            "dayToTake": utils.date_to_str(day),
            "zoneId": zone_id,
            "deskIdOrNull": desk_id,
        }
        return self._post(self.TAKE_DESK_URL, payload)

    def release_desk(self, day: datetime):
        payload = {"daysToShare": utils.date_to_str(day)}
        return self._post(self.RELEASE_DESK_URL, payload)

    def get_zone_image(self, zone_id: str) -> io.BytesIO:
        url = self.GET_ZONE_IMAGE_URL + zone_id
        response = self.session.get(url)
        if response.status_code == 200:
            return io.BytesIO(response.content)

    def get_my_reservations(self):
        return self._get(self.GET_MY_RESERVATIONS_URL)["reservations"]

    def search_colleague(self, query: str) -> list[dict]:
        payload = {"fullNameQuery": query}
        return self._post(self.SEARCH_COLLEAGUE_URL, payload)["foundEmployees"]
