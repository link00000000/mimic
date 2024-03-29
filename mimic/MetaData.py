"""
Metadata pertaining to a video stream.

Raises:
    KeyError: A required key is missing from the JSON string
"""
import json


class MetaData:
    """Metadata pertaining to a video stream."""

    def __init__(self, json_str: str):
        """
        Parse video stream metadata to an object.

        Args:
            json_str (str): JSON object as a string

        Raises:
            KeyError: A required key is missing from the JSON string
        """
        json_obj = json.loads(json_str)

        if 'width' not in json_obj:
            raise KeyError("Required key `width` not in metadata.")
        self.width: int = json_obj['width']

        if 'height' not in json_obj:
            raise KeyError("Required key `height` not in metadata.")
        self.height: int = json_obj['height']

        if 'framerate' not in json_obj:
            raise KeyError("Required key `framerate` not in metadata.")
        self.framerate: int = json_obj['framerate']
