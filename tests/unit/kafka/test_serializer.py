""" Testing suite for the JSONSerializer class """

from managers.kafka._serializer import JSONSerializer


class MockClass:  # pylint:disable=too-few-public-methods
    """A mocked class used for creating complex dependency chains"""

    def __init__(self, dep_1: any = None, dep_2: any = None):
        self.dep_1 = dep_1
        self.dep_2 = dep_2


class MockClassWithAsDict:  # pylint:disable=too-few-public-methods
    """A mocked class that implements an as_dict method"""

    def __init__(self, dep_1: str = None, dep_2: int = None):
        self.dep_1 = dep_1
        self.dep_2 = dep_2
        self.called_as_dict: bool = False

    def as_dict(self) -> str:
        """The as_dict method"""
        self.called_as_dict = True
        return {"dep_1": self.dep_1, "dep_2": self.dep_2}


class TestJsonSerializer:
    """Testing suite"""

    def test_should_serialize_correctly_given_valid_data(self) -> None:
        """
        Given valid data, the serializer should return valid serialized data
        """
        serializer = JSONSerializer()

        test_data = {
            "test": (
                [1, 2, "3", False],
                ("a", "b", "c", "d"),
                {(1, 2), (3, 4)},
                {"a": MockClass(None, 2), "b": MockClass(MockClass(), "Test")},
            )
        }

        serialized_test_data: str = serializer.serialize("test", test_data)

        assert isinstance(serialized_test_data, str)

    def test_should_encode_given_valid_serialized_data(self) -> None:
        """
        Given valid serialized data, the encoder should return bytes
        """
        serializer = JSONSerializer()

        test_data = [MockClass(MockClass(), None), "Test", 3, False, 3.14159]

        serialized_data: str = serializer.serialize("Test", test_data)
        encoded_data: bytes = serializer.encode(serialized_data)

        assert isinstance(encoded_data, bytes)

    def test_should_serialize_and_encode_given_valid_data(self) -> None:
        """
        Given valid data, serialize_and_encode should take a string and return bytes
        """
        serializer = JSONSerializer()

        raw_data = {
            "test": (
                [1, 2, "3", False],
                ("a", "b", "c", "d"),
                {(1, 2), (3, 4)},
                {"a": MockClass(None, 2), "b": MockClass(MockClass(), "Test")},
            )
        }

        encoded_data = serializer.serialize_and_encode("Test", raw_data)

        assert isinstance(encoded_data, bytes)

    def test_should_use_as_dict_method(self) -> None:
        """
        Given a class that implements the as_dict method, it should be used in the serialization
        process.
        """
        serializer = JSONSerializer()
        mocked_class = MockClassWithAsDict("test", 10)

        raw_dict = {"test": True, "test_b": None, "test_c": mocked_class}

        serializer.serialize_and_encode("Test", raw_dict)

        assert mocked_class.called_as_dict is True
