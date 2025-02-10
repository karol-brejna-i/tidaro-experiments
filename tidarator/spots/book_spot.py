from .spot_manager import SpotCacheManager
from .zone_manager import ZoneCacheManager
from ..actions.action_base import ParkanizerActionBase
from ..api.utils import str_to_date
from ..log_config import get_logger

logger = get_logger(__name__)


class BookSpot(ParkanizerActionBase):

    def __init__(self, session, payload: dict[str, str | list[str]]):
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

    def _expand_spot_selection(self, zone_id, preference_input, spots_state):
        """
        Translate spot names to IDs ('choose any' -> None).
        Take only free spots.
        """

        available_items = list([spot['name'] for spot in spots_state if spot['free']])
        result = []

        for preference in preference_input:
            if preference == '*':
                result.append(None)
                break
            elif preference in available_items:
                spot = self.spot_manager.get_by_name(zone_id, preference)
                result.append(spot.get("id"))

        return result if result else None

    def do_for_payload(self, p: dict[str, str | list[str]]) -> dict:
        logger.info(f'Booking a spot for the payload: {p}')

        # get objects' IDs
        zone = self.zone_manager.get_by_name(p['zone_name'])
        zone_id = zone.get('id') if zone else None

        spots = p['spot_name']
        if type(spots) is str:
            spots = [spots]

        spots_states = self.spot_manager.get_spots_state(zone_id, str_to_date(p['for_date']))
        spot_ids = self._expand_spot_selection(zone_id, spots, spots_states)

        logger.debug(f'Zone ID: {zone_id}; Spot IDs: {spot_ids}')

        result: dict[str, dict] = {'action': 'book_spot', 'request': p}
        success = False
        failures = []
        for spot_id in spot_ids:
            try:
                response = self.session.take_spot(zone_id, spot_id, p['for_date'])
                if 'status' in response:
                    if response['status'] == 'Reserved':
                        reservation = response['receivedParkingSpotOrNull']
                        if reservation:
                            result['result'] = {
                                'zone': zone['name'],
                                'spot': reservation['name'],
                                'for_date': p['for_date'],
                                'status': 'success'
                            }
                        else:
                            # This should never happen
                            result['result'] = {'status': 'success',
                                                'note': 'Could not get the reservation status from API response...'}

                        self.notify_listeners('success', result)
                        success = True
                        break
                    else:
                        failures.append(f"Couldn't reserve spot {spot_id} for {p['for_date']}")

            except Exception as e:
                self.notify_listeners('error', {'error': str(e)})
        if not success:
            result['result'] = {
                'status': 'failure',
                'messages': failures
            }
            self.notify_listeners('failure', failures)

        return result

    def do(self):
        return self.do_for_payload(self.payload)
