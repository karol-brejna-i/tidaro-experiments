class DummyNotifier(object):
    """
    Notifier object that is able to send messages to a Gmail account.
    It is initialized with sender email address and password.
    """

    def __init__(self, logger_method):
        """

        :param logger_method: for example `logging.info` or `print`
        """
        self.logger_method = logger_method

    def send_notification(self, event_type, data):
        self.logger_method(f'DUMMY: {event_type}, {data}')
