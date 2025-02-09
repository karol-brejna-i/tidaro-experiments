from .bookings_manager import BookingsCacheManager
from .zone_manager import ZoneCacheManager
from ..actions.action_base import ParkanizerActionBase
from ..log_config import get_logger

logger = get_logger(__name__)


class ShowBookings(ParkanizerActionBase):
    def __init__(self, session, payload: dict):
        super().__init__(session, payload)
        self.zone_manager = ZoneCacheManager(session)  # TODO Think about singleton if you want to combine actions
        self.booking_manager = BookingsCacheManager(session)
        logger.info(f'Payload: {self.payload}')

    def do(self):
        logger.info(f'Get booking info for: {self.payload}')
        # get objects' IDs
        zone = self.zone_manager.get_by_name(self.payload['zone_name'])
        zone_id = zone.get('id') if zone else None

        result: dict[str, dict | list] = {'action': 'show_bookings', 'request': self.payload}
        try:
            response = self.booking_manager.get_bookings(zone_id)
            result['result'] = {
                'status': 'success',
                'bookings': list(response),
                'message': f"Retrieved booking info successfully"
            }
            self.notify_listeners('success', result)

        except Exception as e:
            result['result'] = {
                'status': 'error',
                'error': str(e)
            }
            self.notify_listeners('error', result)

        return result
