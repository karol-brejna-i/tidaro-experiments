from .spot_manager import SpotCacheManager
from .zone_manager import ZoneCacheManager
from ..actions.action_base import ParkanizerActionBase
from ..api.utils import str_to_date
from ..log_config import get_logger

import json

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
        unavailable_items = list([spot['name'] for spot in spots_state if not spot['free']])
        logger.info(f'Spot selection: preferences={preference_input}, '
                    f'available={available_items}, taken={unavailable_items}')
        result = []

        for preference in preference_input:
            if preference == '*':
                logger.info(f'Wildcard preference — will request any free spot')
                result.append(None)
                break
            elif preference in available_items:
                spot = self.spot_manager.get_by_name(zone_id, preference)
                logger.info(f'Preference "{preference}" is available — resolved to ID {spot.get("id")}')
                result.append(spot.get("id"))
            else:
                logger.info(f'Preference "{preference}" is NOT available — skipping')

        logger.info(f'Final spot selection order (IDs): {result}')
        return result

    def do_for_payload(self, p: dict[str, str | list[str]]) -> dict:
        logger.info(f'Booking a spot for the payload: {p}')

        # get objects' IDs
        zone = self.zone_manager.get_by_name(p['zone_name'])
        zone_id = zone.get('id') if zone else None

        spots = p['spot_name']
        if type(spots) is str:
            spots = [spots]

        spots_states = self.spot_manager.get_spots_state(zone_id, str_to_date(p['for_date']))
        logger.debug(f'Spot states: {json.dumps(spots_states)}')

        spot_ids = self._expand_spot_selection(zone_id, spots, spots_states)
        logger.info(f'Booking attempt for {p["for_date"]}: zone_id={zone_id}, '
                    f'spot_ids_to_try={spot_ids} (preference order)')

        result: dict[str, dict] = {'action': 'book_spot', 'request': p}
        success = False
        failures = []
        for spot_id in spot_ids:
            requested_spot_name = next(
                (s['name'] for s in spots_states if s['id'] == spot_id), spot_id
            )
            logger.info(f'Attempting to book spot "{requested_spot_name}" (id={spot_id}) '
                        f'for {p["for_date"]}')
            try:
                response = self.session.take_spot(zone_id, spot_id, p['for_date'])
                logger.debug(f'API response for take_spot({spot_id}): {json.dumps(response)}')

                if 'status' not in response:
                    msg = (f'API response for spot "{requested_spot_name}" (id={spot_id}) '
                           f'has no "status" key! Response: {json.dumps(response)}')
                    logger.warning(msg)
                    failures.append(msg)
                    continue

                if response['status'] == 'Reserved':
                    reservation = response['receivedParkingSpotOrNull']
                    if reservation:
                        booked_name = reservation['name']
                        if booked_name != requested_spot_name:
                            logger.warning(
                                f'MISMATCH: requested spot "{requested_spot_name}" '
                                f'but API reserved "{booked_name}"!'
                            )
                        result['result'] = {
                            'zone': zone['name'],
                            'spot': booked_name,
                            'for_date': p['for_date'],
                            'status': 'success'
                        }
                        logger.info(f'Successfully booked spot "{booked_name}" '
                                    f'for {p["for_date"]}')
                    else:
                        result['result'] = {'status': 'success',
                                            'note': 'Could not get the reservation '
                                                    'status from API response...'}
                        logger.warning(f'Spot reserved but receivedParkingSpotOrNull '
                                       f'is None. Full response: {json.dumps(response)}')

                    self.notify_listeners('success', result)
                    success = True
                    break
                else:
                    msg = (f'Could not reserve spot "{requested_spot_name}" '
                           f'(id={spot_id}) for {p["for_date"]}: '
                           f'status={response["status"]}')
                    logger.info(msg)
                    failures.append(msg)

            except Exception as e:
                msg = (f'Exception booking spot "{requested_spot_name}" '
                       f'(id={spot_id}) for {p["for_date"]}: {e}')
                logger.error(msg, exc_info=True)
                failures.append(msg)
                self.notify_listeners('error', {'error': str(e)})

        if not success:
            logger.warning(f'All spot booking attempts failed for {p["for_date"]}: '
                           f'{failures}')
            result['result'] = {
                'status': 'failure',
                'messages': failures
            }
            self.notify_listeners('failure', failures)

        return result

    def do(self):
        return self.do_for_payload(self.payload)
