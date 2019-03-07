import Pyro4
from Pyro4 import errors
from Exceptions import *


class Client(object):
    def __init__(self):
        print('\nWelcome to the movie rating database!')
        print('\nFollow the on-screen instructions or enter "quit" at any time to disconnect!')
        self.front_end = None

    def send_request(self, request: list):
        # handle possible errors when sending the request - e.g. front end server has gone offline
        try:
            response = self.front_end.forward_request(request)
            return response
        except errors.CommunicationError as error_message:
            print(error_message)
            return 'Cannot communicate with server'

    def get_request(self, operation=None, movie=None, user_id=None, rating=None):
        options = ['READ', 'SUBMIT', 'UPDATE', 'DELETE', 'QUIT']
        while operation not in options:
            operation = input('\nSelect an operation - READ / SUBMIT /'
                              ' UPDATE / DELETE : ').strip().upper()
            if not operation:
                print('Operation cannot be empty! Enter READ, SUBMIT, UPDATE or DELETE\n')
            elif operation not in options:
                print('Invalid input! Enter READ, SUBMIT, UPDATE or DELETE\n')

        if operation == 'QUIT':
            return
        # -----------------------------------------------------------
        while not movie:
            movie = input('\n' + operation.capitalize() +
                          ' ratings for which movie? Provide an ID or title: ').strip()
            if not movie:
                print('ID / title cannot be empty! Provide an ID such'
                      'as "1" or a title such as "Toy Story"\n')

        if movie.upper() == 'QUIT':
            return
        # -----------------------------------------------------------
        while not user_id:
            user_id = input('\n' + operation.capitalize() + ' "' + str(movie).capitalize() +
                            '" rating for which user? Enter user ID: ').strip()
            if not user_id:
                print('User ID cannot be empty! Submit an ID such as "1"')

        if user_id.lower() == 'QUIT':
            return
        # -----------------------------------------------------------
        if operation in ['SUBMIT', 'UPDATE']:
            while not rating:
                rating = input('\nEnter a rating for "' + str(movie) + '": ').strip()
                if rating:
                    try:
                        rating = float(rating)
                        if 5 < rating < 0:
                            print('Rating should be a number between 0 and 5!')
                    except ValueError:
                        if rating.upper() == 'QUIT':
                            break
                        print('Rating "' + str(rating) + '" is not a number!')
                else:
                    print('Rating cannot be empty! Submit a number between 0 and 5')

        if str(rating).upper() == 'QUIT':
            return
        # -----------------------------------------------------------
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


if __name__ == '__main__':
    try:
        URI = Pyro4.resolve("PYRONAME:front_end_server")
        CLIENT = Client()
        CLIENT.front_end = Pyro4.Proxy(URI)
        CLIENT.get_request()
    except errors.NamingError:
        print('Make sure that service is running first!')
