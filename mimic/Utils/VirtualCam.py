"""Utility functions for the virtual camera."""
import winreg

REG_PATH = r"CLSID\{860BB310-5D01-11d0-BD3B-00A0C911CE86}\Instance\{27B05C2D-93DC-474A-A5DA-9BBA34CB2A9C}"

def change_webcam_name(name: str = 'Mimic'):
    """
    Change the name associated with the camera by accessing its registry.

    There is the possibility of permission issues if the the user is not
    have full control of the camera registry entry

    Params:
        name (str): the desired name of the camera (defaults to Mimic)
    """
    reg = winreg.ConnectRegistry(None, winreg.HKEY_CLASSES_ROOT)
    obs_reg = winreg.OpenKey(reg, REG_PATH, 0, winreg.KEY_SET_VALUE)
    winreg.SetValueEx(obs_reg, "FriendlyName", 0, winreg.REG_SZ, name)
