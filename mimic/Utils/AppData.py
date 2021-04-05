"""Operations pertaining to windows AppData paths."""
import os
from pathlib import Path
from typing import Optional, Union

__APPLICATION_NAME = "mimic"
StrPath = Union[str, os.PathLike[str]]


def initialize_local_app_data(application_name: str = __APPLICATION_NAME):
    """
    Create Local AppData directory if it does not already exist.

    Args:
        application_name (str, optional): Name of direct subdirectory of Local
                                          AppData. Defaults to __APPLICATION_NAME.
    """
    path_obj = Path(resolve_local_app_data(application_name=application_name))
    Path.mkdir(path_obj, parents=True, exist_ok=True)


def mkdir_local_app_data(*path: StrPath, application_name: str = __APPLICATION_NAME):
    """
    Create a directory inside of Local AppData if it does not already exist.

    Args:
        path (StrPath): Relative path inside of Local AppData
        application_name (str, optional): Name of direct subdirectory of Local
                                          AppData. Defaults to __APPLICATION_NAME.
    """
    path_obj = Path(resolve_local_app_data(*path, application_name=application_name))
    Path.mkdir(path_obj, parents=True, exist_ok=True)


def resolve_local_app_data(*path: StrPath, application_name: str = __APPLICATION_NAME) -> StrPath:
    """
    Resolve a file or directory path in Local AppData.

    Args:
        path (StrPath): Relative path inside of Local AppData. If not
                        provided, the application root in Local AppData will be returned
        application_name (str, optional): Name of direct subdirectory of Local
                                          AppData. Defaults to __APPLICATION_NAME.

    Returns:
        StrPath: Absolute path to file or directory in Local AppData
    """
    if len(path) == 0:
        return os.path.join(os.environ['LOCALAPPDATA'], application_name)

    return os.path.join(os.environ['LOCALAPPDATA'], application_name, *path)
