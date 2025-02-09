import logging
import logging.config
import os
import tomllib

from tidarator.config import LOGGING_CONFIG_PATH

_logging_setup = False


def get_logger(name):
    global _logging_setup
    if not _logging_setup:
        setup_logging(LOGGING_CONFIG_PATH)
        _logging_setup = True

    logger = logging.getLogger(name)
    return logger


def setup_logging(config_path, quiet=True):
    """Sets up logging from a TOML configuration file, with environment variable override."""
    try:
        with open(config_path, "rb") as f:
            config = tomllib.load(f)
        logging_config = {"version": 1}
        valid_sections = {"loggers", "handlers", "formatters", "root"}
        for section_name, section_data in config.items():
            if section_name in valid_sections:
                logging_config[section_name] = section_data
            else:
                print(f"WARNING! Unknown section in TOML config: {section_name}")

        # Environment variable override for log level
        log_level_env = os.environ.get("LOG_LEVEL")  # Get from environment
        if log_level_env:
            try:
                log_level = getattr(logging, log_level_env.upper())  # Convert to logging level
                if isinstance(logging_config.get('root'), dict):
                    logging_config['root']['level'] = log_level
                else:
                    logging_config['root'] = {'level': log_level,
                                              'handlers': logging_config.get('root', {}).get('handlers', [])}

                print(f"Log level overridden by environment variable: {log_level_env}")
            except AttributeError:
                print(f"WARNING! Invalid LOG_LEVEL environment variable: {log_level_env}")

        logging.config.dictConfig(logging_config)


    except FileNotFoundError:
        if not quiet:
            print(f"Logging config file not found: {config_path}. Using basic config.")
        logging.basicConfig(level=logging.WARNING)
    except Exception as e:
        print(f"Error loading logging configuration: {e}. Using basic config.")
        logging.basicConfig(level=logging.INFO)
