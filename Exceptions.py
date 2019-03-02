class InvalidInputError(Exception):
    def __init__(self, message, *args):
        self.message = message
        super(InvalidInputError, self).__init__(message, *args)
