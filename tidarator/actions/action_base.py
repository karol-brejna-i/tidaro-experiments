class ParkanizerActionBase(object):

    def __init__(self, session, payload: dict):
        """
        Initialize the class with the session object (used to communicate with the server) and the payload,
        and initialize the listener list for the observer pattern.

        :param session: Session object for accessing the Parkanizer service.
        :param payload: The arguments for performing the action
        """
        self.session = session
        self.payload = payload

        self.event_types = ("success", "failure", "error")
        self._event_listeners = {}
        for event in self.event_types:
            self._event_listeners[event] = []

    def _construct_request_payload(self, params: dict):
        """
        Construct the  payload and for API request and return it.
        """
        raise NotImplementedError()

    def _add_listener_to_event(self, listener, event_type):
        """
        Add a listener to a specific event type.

        :param listener: Callable that takes event type and data.
        :param event_type: The specific event type to add the listener for.
        """
        if event_type not in self._event_listeners:
            self._event_listeners[event_type] = []
        self._event_listeners[event_type].append(listener)

    def register_listener(self, listener, event_type=None):
        """
        Register a new listener for a specific event type or all events if no type is specified.

        :param listener: Callable that takes event type and data.
        :param event_type: The specific event type to listen for ("success", "failure", "error"). Default is None for all.
        """
        if not callable(listener):
            raise ValueError("Listener must be callable")

        if not hasattr(self, "_event_listeners"):
            self._event_listeners = {}

        if event_type is None:
            for event in self.event_types:
                self._add_listener_to_event(listener, event)
        else:
            self._add_listener_to_event(listener, event_type)

    def remove_listener(self, listener, event_type=None):
        """
        Remove an existing listener for a specific event type or all types if no type is specified.

        :param listener: Callable to remove.
        :param event_type: The specific event type to remove the listener from. Default is None for all.
        """
        if hasattr(self, "_event_listeners"):
            if event_type is None:
                for event in list(self._event_listeners.keys()):
                    if listener in self._event_listeners[event]:
                        self._event_listeners[event].remove(listener)
            elif event_type in self._event_listeners and listener in self._event_listeners[event_type]:
                self._event_listeners[event_type].remove(listener)

    def notify_listeners(self, event_type: str, data: dict | list = None):
        """
        Notify all listeners about an event.
    
        :param event_type: The type of event ("success", "failure" or "error").
        :param data: Additional data related to the event.
        """
        if event_type in self._event_listeners:
            for listener in self._event_listeners[event_type]:
                listener(event_type, data)
        else:
            logger.warning(f'Unknown event type: {event_type}')

    def do(self):
        """
        Actual action logic.
        """
        raise NotImplementedError()
