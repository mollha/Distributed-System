class InvalidMovieError(Exception):
    def __init__(self, message, *args):
        self.message = message
        super(InvalidMovieError, self).__init__(message, *args)


class InvalidUserError(Exception):
    def __init__(self, message, *args):
        self.message = message
        super(InvalidUserError, self).__init__(message, *args)