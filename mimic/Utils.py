"""Miscellaneous utility functions."""
import socket
import winreg

REG_PATH = r"CLSID\{860BB310-5D01-11d0-BD3B-00A0C911CE86}\Instance\{27B05C2D-93DC-474A-A5DA-9BBA34CB2A9C}"
def change_camera(name: str = 'Mimic'):
    """
    Change the name associated with the camera by accessing its registry.

    There is the possibility of permission issues if the the user is not
    have full control of the camera registry entry

    Params:
        str: the desired name of the camera (defaults to Mimic)
    """
    try:
        reg = winreg.ConnectRegistry(None, winreg.HKEY_CLASSES_ROOT)
        obs_reg = winreg.OpenKey(reg, REG_PATH, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(obs_reg, "FriendlyName", 0, winreg.REG_SZ, name)
    except:
        print("Could not change the camera's name!")

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
