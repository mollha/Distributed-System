from exceptions import *
from typing import Union
import Pyro4
from Pyro4.errors import ConnectionClosedError, CommunicationError, NamingError


class Client(object):
    def __init__(self):
        print('\nWelcome to the movie rating database!')
        print('\nFollow the on-screen instructions or enter "quit" at any time to disconnect!')
        self.front_end = None

    def send_request(self, request: list) -> Union[str, Exception, None]:
        """
            Send a request from the client to the front-end server to either receive a response
            :param request: A list containing an operation, movie identifier, user_id and a rating
            for submitting and updating reviews (rating is None for read and delete operations)
            :return: Response from the front-end server (an exception, string or NoneType)
        """
        response = self.front_end.forward_request(request)
        return response

    def get_request(self, operation: str = None, movie: str = None,
                    user_id: str = None, rating: float = None) -> None:
        """
            Communicates with the user to get the required information for
            submitting queries and updates
            If any of the parameters are already provided then we don't need to ask for these
            This is useful when there is an error with some of the parameters as we can
            specify that we only want to ask for these parameters again
            :param operation: A NoneType or a string containing READ, SUBMIT, UPDATE, DELETE or QUIT
            :param movie: A NoneType or a string containing a movie identifier
            :param user_id: A NoneType or a string containing a user_id
            :param rating: A NoneType or a float representing a movie rating
        """

        # ------------ GET OPERATION TO PERFORM ON THE DATABASE ---------------
        options = ['READ', 'SUBMIT', 'UPDATE', 'DELETE', 'QUIT']
        while operation not in options:
            operation = input('\nSelect an operation - READ / SUBMIT /'
                              ' UPDATE / DELETE : ').strip().upper()
            if not operation:
                print('Operation cannot be empty! Enter READ, SUBMIT, UPDATE or DELETE\n')
            elif operation not in options:
                print('Invalid input! Enter READ, SUBMIT, UPDATE or DELETE\n')

        # If the input entered was QUIT, then close the client
        if operation == 'QUIT':
            return

        # ---------------------- GET MOVIE ID OR TITLE -------------------------
        while not movie:
            movie = input('\n' + operation.capitalize() +
                          ' ratings for which movie? Provide an ID or title: ').strip()
            if not movie:
                print('ID / title cannot be empty! Provide an ID such'
                      'as "1" or a title such as "Toy Story"\n')

        # If the input entered was QUIT, then close the client
        if movie.upper() == 'QUIT':
            return

        # ---------------------------- GET USER ID ------------------------------
        while not user_id:
            user_id = input('\n' + operation.capitalize() + ' "' + str(movie).capitalize() +
                            '" rating for which user? Enter user ID: ').strip()
            if not user_id:
                print('User ID cannot be empty! Submit an ID such as "1"')

        # If the input entered was QUIT, then close the client
        if user_id.lower() == 'QUIT':
            return

        # -------------------------- GET MOVIE RATING --------------------------
        # Only need to provide a new rating on submit and update operations
        if operation in ['SUBMIT', 'UPDATE']:
            while not rating:
                rating = input('\nEnter a rating for "' + str(movie) + '": ').strip()
                if rating:
                    try:
                        rating = float(rating)
                        if rating > 5 or rating < 0:
                            print('Rating should be a number between 0 and 5!')
                            rating = None
                    except ValueError:
                        if rating.upper() == 'QUIT':
                            break
                        print('Rating "' + str(rating) + '" is not a number!')
                else:
                    print('Rating cannot be empty! Submit a number between 0 and 5')

        # If the input entered was QUIT, then close the client
        if str(rating).upper() == 'QUIT':
            return

        # ----------------- SEND THE REQUEST AND HANDLE ERRORS ----------------
        try:
            response = self.send_request([operation.lower(), movie, user_id, rating])
            if operation == 'READ':
                print(response)
            options = ['Y', 'N', 'QUIT']
            repeat = None
            while repeat not in options:
                repeat = input('\nWould you like to submit a new request?'
                               '  Y / N :  ').strip().upper()
                if not repeat:
                    print('Input cannot be empty! Enter Y to continue or N to quit\n')
                elif repeat not in options:
                    print('Invalid input! Enter Y to continue or N to quit\n')
            if repeat == 'Y':
                self.get_request()
            if repeat in ['N', 'QUIT']:
                print('Goodbye!')
                return
        except InvalidUserError as error:
            print('ERROR: %s' % error.message)
            self.get_request(operation=operation, movie=movie)
            return
        except InvalidMovieError as error:
            print('ERROR: %s' % error.message)
            self.get_request(operation=operation)
            return
        except CommunicationError as error:
            if isinstance(error, ConnectionClosedError):
                print('ERROR: Server closed the connection')
            elif isinstance(error, CommunicationError):
                print('ERROR: Cannot communicate with the server')
            return


if __name__ == '__main__':
    try:
        CLIENT = Client()
        URI = Pyro4.resolve("PYRONAME:front_end_server")
        CLIENT.front_end = Pyro4.Proxy(URI)
        CLIENT.get_request()
    except NamingError:
        print('Make sure that service is running first!')
