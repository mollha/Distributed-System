#!/usr/bin/env python3

import Pyro4
from Pyro4 import errors


# check that input is valid before sending it to front_end_server

# connect to the front end
# On connection, the front end should introduce itself and ask for the users name (this will be the users ID
# ask the user which movie to access ratings for
# After movie info is returned, ask for READ, UPDATE or SUBMIT
# If read, reply with user_ID or all ratings
# On update rating, send user_ID and movie_ID and new rating
# On submit rating, automatically
# TODO improve error messages


class Client(object):
    def __init__(self):
        print('\nWelcome to the movie rating database!')
        self.front_end = self.get_front_end()

    def get_front_end(self):
        try:
            uri = Pyro4.resolve("PYRONAME:front_end_server")
            return Pyro4.Proxy(uri)  # use name server object lookup uri shortcut
        except errors.NamingError:
            print('ERROR: Make sure that the front end server is running first!')

    def send_request(self, request: list):
        # handle possible errors when sending the request - e.g. front end server has gone offline
        try:
            return self.front_end.direct_request(request)
        except errors.CommunicationError:
            self.front_end = self.get_front_end()
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
                movie = input('\n' + operation.capitalize() + ' ratings for which movie? Provide an ID or title: ').strip()
                if movie:
                    response = self.send_request(['FIND', movie])  # it will soon return something
                    # if not a movie, will return an error - need to check here that a connection error didnt occur
                    if isinstance(response, list):
                        movie = response[0]
                        ratings = response[3]
                        total_rating = 0
                        for rating in ratings:
                            total_rating += float(rating[1])
                        average_rating = round(total_rating / len(ratings), 1)
                        print('\n--------- Movie Info ---------\n' +
                              'Title:\t' + movie + '\n' +
                              'Year:\t' + response[1] + '\n' +
                              'Genres:\t' + ", ".join(response[2]) + '\n' +
                              'Average Rating: ' + str(average_rating))
                        break
                    else:
                        print(response)
                else:
                    print('ERROR: ID / title cannot be empty! Provide an ID such as "1",'
                          'or a title such as "Toy Story"\n')

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
                    rating = input('Enter a rating for "' + str(movie) + '": ').strip()
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
                    user_ID = input('\n' + operation.capitalize() + ' rating for "' + str(movie) +
                                    '" for which user? Enter user ID: ').strip()
                    if user_ID:
                        response = self.send_request([operation, movie, user_ID, rating])  # it will soon return something
                        # if not a movie, will return an error - need to check here that a connection error didnt occur
                        print(response)
                        if not response.startswith('ERROR', 0, 5):
                            break
                    else:
                        print('ERROR: User ID cannot be empty! Submit an ID such as "1"')
            while True:
                repeat = input('Would you like to continue - Y / N ? ').strip().upper()
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


Client().main()
# connect to the front end down here
