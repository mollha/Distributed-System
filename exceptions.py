"""
    This module contains my custom exception classes
    for raising errors specific to the movie rating database
    e.g. InvalidMovieError, InvalidUserError
"""

import Pyro4
from Pyro4.util import SerializerBase


# Use serpent serialization
Pyro4.config.SERIALIZER = "serpent"


class InvalidMovieError(Exception):
    """
        This is a custom exception class
        This exception is thrown when there is a problem retrieving a movie
        A description of the issue is provided on initialisation
    """

    def __init__(self, message, *args):
        self.message = message
        super(InvalidMovieError, self).__init__(message, *args)

    def __str__(self) -> str:
        return str(self.to_dict())

    def to_dict(self) -> dict:
        """
            Serpent serialization requires to_dict
            Represent class InvalidMovieError as a dictionary
            :return: A dictionary representation of this InvalidMovieError
        """
        return {
            "__class__": "InvalidMovieError",
            "message": self.message
        }

    @staticmethod
    def to_class(class_name: str, dictionary: dict) -> 'InvalidMovieError':
        """
            This converts a dictionary representing an InvalidMovieError
            to an object of type InvalidMovieError
            :param class_name: parameter is required for serialization
            :param dictionary: dictionary representing an InvalidMovieError
            :return:
        """
        del class_name
        return InvalidMovieError(dictionary["message"])


class InvalidUserError(Exception):
    """
        This is a custom exception class
        This exception is thrown when there is an issue with the provided user_id
        A description of the issue can be provided on initialisation
    """

    def __init__(self, message, *args):
        self.message = message
        super(InvalidUserError, self).__init__(message, *args)

    def __str__(self):
        return str(self.to_dict())

    def to_dict(self) -> dict:
        """
            Serpent serialization requires to_dict
            Represent class InvalidUserError as a dictionary
            :return: A dictionary representation of this InvalidUserError
        """
        return {
            "__class__": "InvalidUserError",
            "message": self.message
        }

    @staticmethod
    def to_class(class_name: str, dictionary: dict) -> 'InvalidUserError':
        """
            This converts a dictionary representing an InvalidUserError
            to an object of type InvalidUserError
            This exception is thrown when there is a problem with the provided user_id
            :param class_name: parameter is required for serialization
            :param dictionary: dictionary representing an InvalidUserError
            :return:
        """
        del class_name
        return InvalidUserError(dictionary["message"])


# Register serialization and deserialization hooks for InvalidUserError and InvalidMovieError
SerializerBase.register_class_to_dict(InvalidUserError, InvalidUserError.to_dict)
SerializerBase.register_dict_to_class("InvalidUserError", InvalidUserError.to_class)
SerializerBase.register_class_to_dict(InvalidMovieError, InvalidMovieError.to_dict)
SerializerBase.register_dict_to_class("InvalidMovieError", InvalidMovieError.to_class)
