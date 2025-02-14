import logging
import sys
from datetime import datetime

import click
from dotenv import load_dotenv

from tidarator.api import utils
from tidarator.api.session_spot import ParkanizerSpotSession
from tidarator.config import load_config, MissingEnvironmentVariableError
from tidarator.log_config import get_logger
from tidarator.notifiers.gmail import GmailNotifier
from tidarator.spots.book_free_spots import BookFreeSpots
from tidarator.spots.release_spot import ReleaseSpot
from tidarator.spots.show_bookings import ShowBookings

load_dotenv()
logger = get_logger(__name__)


def get_logged_session(config):
    parkanizer_spot = ParkanizerSpotSession()
    result = parkanizer_spot.login(config["tidaro"]["user"], config["tidaro"]["password"])
    return parkanizer_spot if result else None


def log_message(event_type, data):
    logging.info(f'{event_type}, {data}')


def print_result(data):
    from tidarator.notifiers.utils import format_results
    text = format_results(data)
    print(text)


def configure_notifiers_for_action(action, config):
    gmail_config = config.get("notifiers", {}).get("gmail")
    if gmail_config:
        recipients = gmail_config["recipient"].split(',')
        if len(recipients) == 1:
            recipients = recipients[0] # keep it consistent with previous implementation
        gn = GmailNotifier(
            gmail_config["user"],
            gmail_config["password"],
            recipients
        )
        action.register_listener(gn.send_notification)


@click.group()
@click.pass_context
def cli(ctx):
    """Tidarator: A command-line tool for managing parking spot bookings on tidaro.com."""
    ctx.ensure_object(dict)
    try:
        ctx.obj['config'] = load_config()
    except MissingEnvironmentVariableError as e:
        logger.error(e)
        print(f"Error: {e}!", file=sys.stderr)
        sys.exit(1)


@cli.command(help="Book a parking spot for a specific date.")
@click.option(
    '-d', '--date',
    default=utils.date_to_str(datetime.today()),
    show_default=True,
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help='Date of the reservation in YYYY-MM-DD format.'
)
@click.pass_context
def book_spot(ctx, date):
    """Book a parking spot."""
    logging.info('run_book_spot')
    config = ctx.obj['config']
    session = get_logged_session(config)

    payload = {
        'for_date': utils.date_to_str(date),
        'zone_name': config["book-spot"]["zone"],
        'spot_name': config["book-spot"]["spots"]
    }
    from tidarator.spots.book_spot import BookSpot
    action = BookSpot(session, payload)
    action.register_listener(log_message)
    result = action.do()

    print_result(result)


@cli.command(help="Release a previously reserved parking spot.")
@click.option(
    '-d', '--date',
    default=utils.date_to_str(datetime.today()),
    show_default=True,
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help='Date of the reservation in YYYY-MM-DD format.'
)
@click.pass_context
def release_spot(ctx, date):
    """Release a parking spot."""
    logging.info('run_release_spot')
    config = ctx.obj['config']
    session = get_logged_session(config)

    payload = {'for_date': utils.date_to_str(date)}

    action = ReleaseSpot(session, payload)
    action.register_listener(log_message)
    result = action.do()

    print_result(result)


@cli.command(help="Show all current bookings for your account.")
@click.pass_context
def show_bookings(ctx):
    """Display current bookings."""
    logging.info('run_show_bookings')
    config = ctx.obj['config']
    session = get_logged_session(config)

    payload = {'zone_name': config["book-spot"]["zone"]}

    action = ShowBookings(session, payload)
    action.register_listener(log_message)
    configure_notifiers_for_action(action, config)
    result = action.do()

    print_result(result)


@cli.command(help="Automatically book free spots within your configured parameters.")
@click.pass_context
def book_free(ctx):
    """Book free spots."""
    logging.info('run_book_free')
    config = ctx.obj['config']
    session = get_logged_session(config)

    payload = {
        'zone_name': config["book-spot"]["zone"],
        'spot_name': config["book-spot"]["spots"],
        'look-ahead': config["check-spots"]["look-ahead"]
    }
    action = BookFreeSpots(session, payload)
    configure_notifiers_for_action(action, config)
    result = action.do()

    print_result(result)

@cli.command(help="Show spots status for a specific date.")
@click.option(
    '-d', '--date',
    default=utils.date_to_str(datetime.today()),
    show_default=True,
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help='Date of interest in YYYY-MM-DD format.'
)
@click.pass_context
def show_spots(ctx, date):
    """Get spots status for a specific date."""
    logging.info('run_show_spots')
    config = ctx.obj['config']
    session = get_logged_session(config)

    payload = {
        'for_date': utils.date_to_str(date),
        'zone_name': config["book-spot"]["zone"]
    }

    from tidarator.spots.show_state import ShowSpotsState
    action = ShowSpotsState(session, payload)
    action.register_listener(log_message)
    result = action.do()

    print_result(result)

if __name__ == "__main__":
    cli()
