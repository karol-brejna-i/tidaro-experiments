# Notifications

This project includes a simple add notifications for the actions it performs.
For example, the user can get an email after successful parking spot reservation.

You can plug in different notification methods, like sending an email or an instant message, to suit your needs.

For implementation details or information how to add custom notifier, see [Implementation](#implementation) section.

## Supported providers

### Gmail Notifications via SMTP

This project enables email notifications using Gmail's SMTP server (via [yagmail](https://pypi.org/project/yagmail/)
package).
It is a simple integration that sends emails from indicated Gmail account (configured email).
It logs to Gmail using email and password.
ATTOW, Google doesn't allow for using "personal" password for the account and use _app password_ instead.
(See <https://knowledge.workspace.google.com/kb/how-to-create-app-passwords-000009237> for info about creating the
password.)

### Required configuration

The following settings are essential for configuring Gmail notificiations:

| key         | description                                    |
|-------------|------------------------------------------------|
| `user`      | Gmail address used to send the messages        |
| `password`  | App password generated for the Gmail account   |
| `recipient` | Email address(es) to receive the notifications |

The corresponding environment variables are:

- NOTIFIERS_GMAIL_USER
- NOTIFIERS_GMAIL_PASSWORD
- NOTIFIERS_GMAIL_RECIPIENT

`recipient` can be a comma separated list of e-mail addresses. 
Example `recipeint` values are 'user1@gmail.com' or 'user1@gmail.com,user2@outlook.com'.