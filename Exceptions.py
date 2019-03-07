import Pyro4
from Pyro4.util import SerializerBase

Pyro4.config.SERIALIZER = "serpent"


class InvalidMovieError(Exception):
    def __init__(self, message, *args):
        self.message = message
        super(InvalidMovieError, self).__init__(message, *args)

    def __str__(self):
        return str(self.to_dict())

    def to_dict(self) -> dict:
        return {
            "__class__": "InvalidMovieError",
            "message": self.message
        }

    @staticmethod
    def to_class(class_name, dictionary: dict):
        return InvalidMovieError(dictionary["message"])


class InvalidUserError(Exception):
    def __init__(self, message, *args):
        self.message = message
        super(InvalidUserError, self).__init__(message, *args)

    def __str__(self):
        return str(self.to_dict())

    def to_dict(self) -> dict:
        return {
            "__class__": "InvalidUserError",
            "message": self.message
        }

    @staticmethod
    def to_class(class_name, dictionary: dict):
        return InvalidUserError(dictionary["message"])


SerializerBase.register_class_to_dict(InvalidUserError, InvalidUserError.to_dict)
SerializerBase.register_dict_to_class("InvalidUserError", InvalidUserError.to_class)
SerializerBase.register_class_to_dict(InvalidMovieError, InvalidMovieError.to_dict)
SerializerBase.register_dict_to_class("InvalidMovieError", InvalidMovieError.to_class)
