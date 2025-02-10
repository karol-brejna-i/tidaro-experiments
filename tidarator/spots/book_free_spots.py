from datetime import datetime, timedelta

from .spot_manager import SpotCacheManager
from .zone_manager import ZoneCacheManager
from ..actions.action_base import ParkanizerActionBase
from ..api import utils
from ..log_config import get_logger

logger = get_logger(__name__)


class BookFreeSpots(ParkanizerActionBase):

    def __init__(self, session, payload: dict):
        """
        Initialize the class with the session_spot object.
        :param session: Session object for accessing the Parkanizer service.
        :param payload: dict with keys: for_date (YYYY-mm-dd), zone_name, spot_name
        """
        super().__init__(session, payload)
        self.zone_manager = ZoneCacheManager(session)
        self.spot_manager = SpotCacheManager(session)
        logger.info(f'Payload: {self.payload}')

    # TODO XXX looks like this is not used....
    def _construct_request_payload(self, params: dict):
        payload = {
            'dayToTake': self.payload['for_date'],
            'parkingSpotZoneId': params['zone_id'],
            'parkingSpotIdOrNull': params['spot_id'],
            'bookingTimeInterval':
                {'fromBookingTime': 'P0DT00H00M', 'toBookingTime': 'P1DT00H00M'}
        }

    def do(self):
        logger.info(f'Booking free spots for the payload: {self.payload}')

        # get objects' IDs
        zone = self.zone_manager.get_by_name(self.payload['zone_name'])
        zone_id = zone.get('id') if zone else None

        from tidarator.spots.show_bookings import ShowBookings
        action = ShowBookings(self.session, self.payload)
        gb_result = action.do()
        bookings = gb_result['result']['bookings']

        # filter out weekends, my current bookings and dates with no free spots
        look_from = datetime.today() + timedelta(days=self.payload["look-ahead"])
        bookings = [
            booking for booking in bookings
            if utils.str_to_date(booking['day']) >= look_from
               and not booking['my_booking']
               and utils.str_to_date(booking['day']).weekday() < 5
               and booking['free_spots'] > 0
        ]

        payload = {
            'zone_name': self.payload['zone_name'],
            'spot_name': self.payload['spot_name']
        }

        from tidarator.spots.book_spot import BookSpot
        book_action = BookSpot(self.session, payload)

        result: dict[str, dict | list] = {'action': 'book_free', 'request': {**self.payload, 'look-from': look_from}}
        attempts = []
        for booking in bookings:
            payload['for_date'] = booking['day']
            attempts.append(book_action.do_for_payload(payload))
        result['result'] = attempts

        self.notify_listeners('success', result)
        return result
