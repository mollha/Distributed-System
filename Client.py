import Pyro4
from Pyro4 import errors


class Client(object):
    def __init__(self):
        print('\nWelcome to the movie rating database!')
        self.front_end = self.get_front_end()
        self.main()

    def get_front_end(self):
        try:
            uri = Pyro4.resolve("PYRONAME:front_end_server")
            self.front_end = Pyro4.Proxy(uri)  # use name server object lookup uri shortcut
            return self.front_end
        except errors.NamingError:
            print('ERROR: Make sure that the front end server is running first!')

    def send_request(self, request: list):
        # handle possible errors when sending the request - e.g. front end server has gone offline
        try:
            # TODO change to a counter
            while True:
                response = self.front_end.direct_request(request)
                if response == 'ERROR: All replicas offline':
                    print(response)
                    print('Reconnecting...\n')
                else:
                    break
            return response
        except IOError as e:
            print(e)
        except errors.CommunicationError as e:
            print(e)
            self.get_front_end()
            return 'ERROR: Cannot communicate with server'

    def main(self):
        while True:
            while True:
                operation = input('\nSelect an operation - READ / SUBMIT / UPDATE / DELETE : ').strip().upper()
                options = ['READ', 'SUBMIT', 'UPDATE', 'DELETE']
                if operation in options:
                    break
                elif not operation:
                    print('ERROR: Operation cannot be empty! Enter READ, SUBMIT, UPDATE or DELETE\n')
                else:
                    print('ERROR: Invalid input! Enter READ, SUBMIT, UPDATE or DELETE\n')

            while True:
                movie = input('\n' + operation.capitalize() +
                              ' ratings for which movie? Provide an ID or title: ').strip()
                if movie:
                    break
                else:
                    print('ERROR: ID / title cannot be empty! Provide an ID such'
                          'as "1" or a title such as "Toy Story"\n')
                return movie

            search = None
            rating = None
            if operation == 'READ':
                while True:
                    search = input('\nShow all ratings for "' + str(movie) +
                                   '" or search by user ID?  ALL / SEARCH : ').strip().upper()
                    if search in ['ALL', 'SEARCH']:
                        response = self.send_request(['READ', movie, None])
                        if not response.startswith('ERROR', 0, 5):
                            if search == 'ALL':
                                print(response)
                            break
                        else:
                            print(response)
                    else:
                        print('ERROR: Invalid input! Enter ALL or SEARCH\n')
            elif operation in ['SUBMIT', 'UPDATE']:
                while True:
                    rating = input('\nEnter a rating for "' + str(movie) + '": ').strip()
                    if rating:
                        try:
                            rating = float(rating)
                            if 0 <= rating <= 5:
                                break
                            else:
                                print('ERROR: Rating should be a number between 0 and 5!')
                        except ValueError:
                            print('ERROR: Rating "' + str(rating) + '" is not a number!')
                    else:
                        print('ERROR: Rating cannot be empty! Submit a number between 0 and 5')
            if operation != 'READ' or search == 'SEARCH':
                while True:
                    user_ID = input('\n' + operation.capitalize() + ' "' + str(movie) +
                                    '" rating for which user? Enter user ID: ').strip()
                    if user_ID:
                        response = self.send_request(
                            [operation, movie, user_ID, rating])  # it will soon return something
                        # if not a movie, will return an error - need to check here that a connection error didnt occur
                        print(response)
                        if not response.startswith('ERROR', 0, 5):
                            break
                    else:
                        print('ERROR: User ID cannot be empty! Submit an ID such as "1"')

            while True:
                repeat = input('\nWould you like to submit a new request?  Y / N  ').strip().upper()
                options = ['Y', 'N']
                if repeat in options:
                    break
                elif not repeat:
                    print('ERROR: Input cannot be empty! Enter Y to continue or N to quit\n')
                else:
                    print('ERROR: Invalid input! Enter Y to continue or N to quit\n')
            if repeat == 'N':
                print('Goodbye!')
                break


Client()
# connect to the front end down here
