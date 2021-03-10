"""Miscellaneous utility functions."""
import socket


def resolve_host() -> str:
    """
    Fetch internal IP address of active network device.

    The active network device is different from the default
    network device. A dummy connection is made to detect
    which network device is actually being used and fetching
    the IP address of that device.

    Adapted from: https://stackoverflow.com/a/166589

    Returns:
        str: Active network device's internal IP address
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))

        host = sock.getsockname()[0]
    except:
        host = "localhost"
    finally:
        sock.close()

    return host
