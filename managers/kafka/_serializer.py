""" The serializer suite. A package-private class that handles serializing data to JSON """

import json
from json import JSONEncoder


class JSONSerializer:
    """The JSON serializer class. Uses the builtin json package"""

    def __init__(self):
        """
        The serializer constructor

        Uses a custom encoder class for handling class objects
        """
        self._encoder_class = JSONObjectEncoder

    def serialize_and_encode(self, event: str, data: any) -> bytes:
        """
        Method to serialize and encode data
        """
        return self.encode(self.serialize(event, data))

    def serialize(self, event: str, data: any) -> str:
        """
        Serializes data into JSON format. Uses JSONObjectEncoder for object serialization.
        """
        try:
            return json.dumps({"event": event, "message": data}, cls=self._encoder_class)
        except ValueError:
            return json.dumps({"event": event, "message": self._encoder_class().default(data)})

    def encode(self, serialized_data: str) -> bytes:
        """
        Takes serialized data as a str and encodes it to utf-8
        """
        return serialized_data.encode()


class JSONObjectEncoder(JSONEncoder):
    """
    A custom encoder class to convert class objects into JSON
    """
    def default(self, o):
        """
        Args:
            o (object): An arbitrary object that must be converted to a dict
        """
        try:
            if callable(getattr(o, "as_dict", None)):
                return o.as_dict()
            if isinstance(o, (str, int, float, bytes, bool, type(None))):
                return o
            if isinstance(o, set):
                return list(o)
            if type(o).__str__ is not object.__str__:
                return str(o)
            if type(o).__repr__ is not object.__repr__:
                return repr(o)
            return dict(vars(o).items())
        except (AttributeError, TypeError):
            return str(o)
        except Exception:  # pylint:disable=broad-exception-caught
            return super().default(o)
