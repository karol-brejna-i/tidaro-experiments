# tidarator

This is an automation tool for booking a parking spot on [tidaro.com](https://www.tidaro.com).

It takes a form of a Python script that can be run as a CLI command or as Docker container.

Please note that although Tidaro.com also offers desk or room bookings, this tool only covers parking spots.

## Usage

Use the utility as a __python script__:

```bash
pip install -r requirements
python tictl.py 
```

You can also build the project, install the resulting package and use (in terminal) as a command:

```
pip install hatch
hatch shell
```

After entering the shell, use __`tidaro` command__:

```bash
~/git-projects/tidaro-experiments$ tidarator

Usage: tidarator [OPTIONS] COMMAND [ARGS]...

  Tidarator: A command-line tool for managing parking spot bookings on
  tidaro.com.

Options:
  --help  Show this message and exit.

Commands:
  book-free      Automatically book free spots within your configured
                 parameters.
  book-spot      Book a parking spot for a specific date.
  release-spot   Release a previously reserved parking spot.
  show-bookings  Show all current bookings for your account.
  show-spots     Show spots status for a specific date.
```

### Book spot

`book-spot` command has the following syntax:

```bash 
$ tidarator book-spot --help
Usage: tidarator book-spot [OPTIONS]

  Book a parking spot for a specific date.

Options:
  -d, --date [%Y-%m-%d]  Date of the reservation in YYYY-MM-DD format.
                         [default: 2025-02-15]
  -s, --spot TEXT        Name of the spot (may be many values) to book (or "*"
                         for "book any").
  --help                 Show this message and exit.
```

Example invocations:

- `tidarator book-spot --spot 25` -- book spot '25' for today
- `tidarator book-spot --spot 25 --spot 11` -- try to book spot '25', then try '11', quit if they are not free
- `tidarator book-spot --spot '*'` -- book any available spot for today
- `tidarator book-spot -s 02 -s 03 -s '*'` -- try '02', '03' then try booking any available spot if they are not free
- `tidarator book-spot --date 2025-05-01 --spot 11` -- book '11' for the first of May

### Release spot

`release-spot` usage:
```
Usage: tidarator release-spot [OPTIONS]

  Release a previously reserved parking spot.

Options:
  -d, --date [%Y-%m-%d]  Date of the reservation in YYYY-MM-DD format.
                         [default: 2025-02-15]
  --help                 Show this message and exit.
```

Example invocations:

- `tidarator release-spot` -- release a spot booked for today
- `tidarator release-spot --date 2025-05-01` -- release a spot booked for 2025-05-01.

### Show spots

`show-spots` command is used for showing parking spots state for a given day:

```
Usage: tidarator show-spots [OPTIONS]

  Show spots status for a specific date.

Options:
  -d, --date [%Y-%m-%d]  Date of interest in YYYY-MM-DD format.  [default:
                         2025-02-15]
  --help                 Show this message and exit.
```

Example usage:
- `tidarator show-spots ` -- show spots state for today
- `tidarator show-spots --date 2025-05-01` -- show spots for 2025-05-01

## Configuration

Please, note that the app requires some configuration in order to run.
It reads specific environment variables.

You should set the env before you run `tidarator`.
The app also tries to read `.env` file, so you can place them there.

### Basic Configuration

The basic configuration settings that allow
for connecting to the Tidaro service and make bookings according to user's preferences.

| env               | description                                                    |
| ----------------- | -------------------------------------------------------------- |
| `TIDARO_USER`     | Email of tidaro.com user's account.                            |
| `TIDARO_PASSWORD` | Password for tidaro.com account.                               |
| `SPOT_ZONE`       | The name of the parking spot area in the Tidaro service.       |
| `SPOT_NAMES`      | Comma-separated list of preferred spot names ('*' == book any) |
| `LOOK_AHEAD`      | Number of days to look ahead (default: 7).                     |

`SPOT_ZONE` is the value you can observe in tidaro.com service (https://share.parkanizer.com/marketplace, "Choose
parking spot area" dropdown box).

`SPOT_NAMES` is a comma separated list of spot names (as you would see them when booking a spot).
The order of the spots here is significant. It reflects the preferences of the user. The logic is:
try the first spot, if it's not available, try the next one, etc.

Here are some example values with explanation:

- '*' -- book any free spot
- '25,08' -- try 25, then 08 and give up when they are not free
- '25,08,*' -- try 25, then 08 or book any if those are not available

Environment variables that names start with `NOTIFIERS_` are responsible for
configuring notifications. Currently only Gmail notifier is implemented.

| env                         | description                                 |
| --------------------------- | ------------------------------------------- |
| `NOTIFIERS_GMAIL_USER`      | Email address to send notifications from.   |
| `NOTIFIERS_GMAIL_PASSWORD`  | App password for the sending email address. |
| `NOTIFIERS_GMAIL_RECIPIENT` | Email address(es) to receive notifications. |

For detailed instructions on setting up Gmail notifications, see
the [notifications documentation](docs/notifications.md).

### Technical Settings

These settings control the application's technical behavior.

| env                   | description                                          |
| --------------------- | ---------------------------------------------------- |
| `SESSION_SECRETS_DIR` | Directory to store session secrets for faster login. |
| `LOGGING_CONFIG_PATH` | Path to the `.toml` file with logging configuration. |

To improve login speed, the application stores session secrets from previous login attempts. You can configure the
directory where these secrets are stored using `SESSION_SECRETS_DIR`.

Normally, as a command line utility `tidarator` sends output to the console.
There are cases (for example, when the utility is run as a scheduled job), where
more advanced logging is required.
`LOGGING_CONFIG_PATH` is a path to toml configuration file to set up logging for the app.

Take a look at [example config](tidarator/logging.toml) to see example use of console and file handlers.
If logging config is not provided, defaults are used.

## Dockerization

You can also take a look at [the docs](docs/dockerization/build_and_run.md) to see how to run the app as a docker
container.

## TODO

Technical:

- bookings should not be cached

Features:

- in-app scheduler? (right now it is a simple atomic action logic. scheduling is done externally -- cron, etc.),
  there is no logic involved so retrying and similar stuff are not easy to achieve)

