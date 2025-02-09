import pickle

from requests import Session

from . import auth
from ..config import SESSION_SECRETS_DIR
from ..log_config import get_logger

logger = get_logger(__name__)
PARKANIZER_API = "https://share.parkanizer.com/api"


class ParkanizerSessionBase:
    def __init__(self):
        self.session: Session = Session()

    def login(self, username: str, password: str):
        result = False
        try:
            logger.info("Trying to authenticate with stored secrets")

            # TODO should this be isolated/removed from "pure" session logic
            with open(SESSION_SECRETS_DIR / "session_secrets", "rb") as f:
                session_secrets = pickle.load(f)

            self._set_secrets(*(session_secrets.values()))
            self._try_refresh_token()
            logger.info("Successfully authenticated with stored secrets")
            result = True
        except (FileNotFoundError, pickle.UnpicklingError, KeyError, EOFError, TypeError):
            logger.info("Failed to authenticate with stored secrets. Trying with normal login.")
            session_secrets = auth.get_token(username, password)
            logger.info("Authenticated with username and password")
            self._set_secrets(*(session_secrets.values()))
            result = True

        if not result:
            raise Exception("Failed to authenticate with username and password")
        else:
            with open(SESSION_SECRETS_DIR / "session_secrets", "wb") as f:
                pickle.dump(session_secrets, f)
        return result

    def _try_refresh_token(self):
        url = PARKANIZER_API + "/auth0/try-refresh-token"
        response = self.session.post(url, json={})
        self._set_secrets(response.json()["newTokenOrNull"]["accessToken"], response.cookies["refresh_token"], )

    def get_my_context(self):
        url = PARKANIZER_API + "/get-employee-context"
        payload = {}
        return self._post(url, payload)

    def _post(self, url, payload=None) -> dict:
        response = self.session.post(url, json=payload)
        if response.text:
            return response.json()
        else:
            return {}

    def _get(self, url) -> dict:
        return self.session.get(url).json()

    def _set_secrets(self, bearer_token, access_token):
        self.session.headers.update({"Authorization": "Bearer " + bearer_token})
        self.session.cookies.update({"refresh_token": access_token})
