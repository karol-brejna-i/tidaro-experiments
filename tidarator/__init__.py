"""Tidarator — CLI tool for managing Tidaro.com parking spot bookings."""

try:
    from tidarator._version import __version__
except ImportError:
    # Fallback for editable installs / development without build
    from importlib.metadata import version, PackageNotFoundError

    try:
        __version__ = version("tidarator")
    except PackageNotFoundError:
        __version__ = "0.0.0-dev"
