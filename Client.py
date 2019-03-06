from Pyro4 import errors
from Exceptions import *
import Pyro4


class Client(object):
    def __init__(self):
        print('\nWelcome to the movie rating database!')
        print('\nFollow the on-screen instructions or enter "quit" at any time to disconnect!')
        client.front_end = client.get_front_end()
        self.get_request()

    def get_front_end(self):
        try:
            uri = Pyro4.resolve("PYRONAME:front_end_server")
            self.front_end = Pyro4.Proxy(uri)  # use name server object lookup uri shortcut
            return self.front_end
        except errors.NamingError:
            print('Make sure that service is running first!')

    def send_request(self, request: list):
        # handle possible errors when sending the request - e.g. front end server has gone offline
        try:
            while True:
                response = self.front_end.forward_request(request)
                if response == 'ERROR: All replicas offline':
                    print(response)
                    print('Reconnecting...\n')
                else:
                    break
            return response
        except errors.CommunicationError as e:
            print(e)
            self.get_front_end()
            return 'Cannot communicate with server'

    def get_request(self, operation=None, movie=None, user_id=None, rating=None):
            options = ['READ', 'SUBMIT', 'UPDATE', 'DELETE', 'QUIT']
            while operation not in options:
                operation = input('\nSelect an operation - READ / SUBMIT / UPDATE / DELETE : ').strip().upper()
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
                user_id = input('\n' + operation.capitalize() + ' "' + str(movie) +
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
                print(operation.lower(), movie, user_id, rating)
                response = self.send_request([operation.lower(), movie, user_id, rating])
                if operation == 'READ':
                    print(response)
                # if not a movie, will return an error - need to check here that a connection error didnt occur
                options = ['Y', 'N', 'QUIT']
                repeat = None
                while repeat not in options:
                    repeat = input('\nWould you like to submit a new request?  Y / N :  ').strip().upper()
                    if not repeat:
                        print('Input cannot be empty! Enter Y to continue or N to quit\n')
                    elif repeat not in options:
                        print('Invalid input! Enter Y to continue or N to quit\n')
                if repeat == 'Y':
                    self.get_request()
                if repeat == 'N' or repeat == 'QUIT':
                    print('Goodbye!')
                    return
            except InvalidMovieError as error:
                print('ERROR: %s' % error.message)
                self.get_request(operation=operation)
                return
            except InvalidUserError as error:
                print(error.message)
                print('got here')
                self.get_request(operation=operation, movie=movie)
                return


if __name__ == '__main__':
    client = Client()
# connect to the front end down here

# TODO invalid user error being excepted as invalid movie error
