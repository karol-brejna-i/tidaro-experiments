from ..log_config import get_logger

logger = get_logger(__name__)

from ..actions.action_base import ParkanizerActionBase


class ReleaseSpot(ParkanizerActionBase):

    def __init__(self, session, payload: dict[str, str]):
        """
        Initialize the class with the session_spot object.
        :param session: Session object for accessing the Parkanizer service.
        :param payload: dict with keys: for_date (YYYY-mm-dd), zone_name, spot_name
        """
        super().__init__(session, payload)
        logger.info(f'Payload: {self.payload}')

    # TODO XXX it seems not to be used...
    def _construct_request_payload(self, params: dict[str, str]):
        return {"daysToShare": [self.payload['for_date']], "receivingEmployeeIdOrNull": None}

    def do(self):
        logger.info(f'Releasing a spot for the payload: {self.payload}')

        result: dict[str, dict] = {'action': 'release_spot', 'request': self.payload}
        try:
            response = self.session.release_spot(self.payload['for_date'])
            if not response:
                result['result'] = {
                    'status': 'success',
                    'message': f"Released spot for {self.payload['for_date']} successfully"}
                self.notify_listeners('success', result)

        except Exception as e:
            result['result'] = {'status': 'error', 'error': str(e)}
            self.notify_listeners('error', result)

        return result
