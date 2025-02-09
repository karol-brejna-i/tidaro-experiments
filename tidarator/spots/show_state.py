from .spot_manager import SpotCacheManager
from .zone_manager import ZoneCacheManager
from ..actions.action_base import ParkanizerActionBase
from ..api.utils import str_to_date
from ..log_config import get_logger

logger = get_logger(__name__)


class ShowSpotsState(ParkanizerActionBase):

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

    def do_for_payload(self, p: dict[str, str | list[str]]) -> dict:
        logger.info(f'Getting spots state for the payload: {p}')

        zone = self.zone_manager.get_by_name(p['zone_name'])
        zone_id = zone.get('id') if zone else None

        result: dict[str, dict] = {'action': 'show_spots', 'request': p}

        try:
            spots = self.spot_manager.get_spots_state(zone_id, str_to_date(p['for_date']))
            result['result'] = {
                'zone': zone['name'],
                'for_date': p['for_date'],
                'spots': spots,
                'status': 'success'
            }

            self.notify_listeners('success', result)

        except Exception as e:
            self.notify_listeners('error', {'error': str(e)})

        return result

    def do(self):
        return self.do_for_payload(self.payload)
