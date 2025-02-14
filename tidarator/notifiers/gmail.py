import yagmail

from tidarator.log_config import get_logger
from tidarator.notifiers.utils import format_results

logger = get_logger(__name__)


class GmailNotifier(object):
    """
    Notifier object that is able to send messages to a Gmail account.
    It is initialized with sender email address and password.
    """

    def __init__(self, sender, password, recipient):
        self.sender = sender
        self.password = password
        self.recipient = recipient
        if isinstance(self.recipient, str):
            self.recipient = [self.recipient]
        self.yag = yagmail.SMTP(sender, password)
        logger.info('gmail notifier initialized')

    def _construct_message_body(self, event_type, data):
        body = ''
        if event_type == 'error':
            body += f'Parkanizer Bot notification: Error! {data["result"]["error"]}'
        else:
            body += format_results(data)
        return body

    def send_notification(self, event_type, data):
        logger.info('sending notification to gmail')
        subject = f'Parkanizer Bot notification'
        body = self._construct_message_body(event_type, data)
        body += '\n\n https://share.parkanizer.com/reservations-list'

        # if recipient is a string, make it a list
        for r in self.recipient:
            result = self.yag.send(to=r, subject=subject, contents=body)
            logger.debug(f'gmail notification sending to {r} status:{str(result)}')

