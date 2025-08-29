import os
import pathlib


class MissingEnvironmentVariableError(Exception):
    def __init__(self, env_name):
        self.env_name = env_name
        super().__init__(f"Missing environment variable: {env_name}")


def get_env_or_crash(env_name):
    env = os.environ.get(env_name)
    if not env:
        raise MissingEnvironmentVariableError(env_name)
    return env


def get_path_or_default(env_name, default=None):
    env = os.environ.get(env_name)
    if env:
        return pathlib.Path(env).resolve()
    else:
        return default


# for quicker logging process, after successful login the secrets are stored in a file to be reused next time
# in current implementation the file resides in the same folder as the main package (tidarator)
SESSION_SECRETS_DIR = get_path_or_default("SESSION_SECRETS_DIR", pathlib.Path(__file__).parents[0].resolve())
LOGGING_CONFIG_PATH = get_path_or_default("LOGGING_CONFIG_PATH", "logging.toml")
LOG_DIR = get_path_or_default("LOG_DIR", pathlib.Path(__file__).parents[1].resolve())


def parse_notifiers():
    notifiers = {}

    for key, value in os.environ.items():
        if key.startswith("NOTIFIERS_"):
            _, notifier_type, field = key.split("_", 2)
            notifier_type = notifier_type.lower()

            if notifier_type not in notifiers:
                notifiers[notifier_type] = {}

            notifiers[notifier_type][field.lower()] = value

    return notifiers


def load_config():
    spots_env = get_env_or_crash("SPOT_NAMES")
    # cleanup the names (trim, remove surrounding quotes)
    spots = [name.strip().strip("'") for name in spots_env.split(",") if name.strip()]

    notifiers = parse_notifiers()

    config = {
        "tidaro": {
            "user": get_env_or_crash("TIDARO_USER"),
            "password": get_env_or_crash("TIDARO_PASSWORD")
        },

        'book-spot': {
            "zone": get_env_or_crash("SPOT_ZONE"),
            "spots": spots
        },
        'check-spots': {'look-ahead': int(os.getenv("LOOK_AHEAD", 0))},
        'notifiers': notifiers
    }

    return config
