# Client.py

import Pyro4

# set up a connection
front_end = Pyro4.Proxy("PYRONAME:front_end_server")    # use name server object lookup uri shortcut
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
        valid_name = False
        while not valid_name:
            self.name = self.clean_input(input('Enter your name: '))
            if self.name:
                valid_name = True
            else:
                print('Name cannot be empty!\n')
        print('Hello ' + self.name + '!')
        # TODO validate name and check user_ID doesn't already exist

    def get_movie(self):
        valid_movie = False
        while not valid_movie:
            movie = self.clean_input(input('Access ratings for which movie? Provide an ID or title: '))
            if movie:
                valid_movie = True
            else:
                print('ID / Title cannot be empty!\n')
        print('Excellent choice!')

    def get_operation(self, input_string):
        valid_operation = False
        operations = ['READ', 'SUBMIT', 'UPDATE']
        while not valid_operation:
            movie = self.clean_input(input('Access ratings for which movie? Provide an ID or title: '))
            if movie:
                valid_movie = True
            else:
                print('ID / Title cannot be empty!\n')
        print('Excellent choice!')
        pass

    def clean_input(self, input_string):
        input_string = input_string.strip('"'"'"' ')  # strips leading and trailing whitespace and commas
        while '  ' in input_string:  # while there are double whitespaces within artist name
            input_string = input_string.replace('  ', ' ')  # replace them with a single whitespace
        return input_string


    def main(self):
        while True:
            movie = self.clean_input(input('Access ratings for which movie? Provide an ID or title: '))
            if movie:
                break
            else:
                print('ID / Title cannot be empty!\n')
        # contact front end and ask for the movie information
        response = front_end.direct_request(['FIND', movie])
        print(response)
        # print(whatever is returned)
        # if response.startswith('ERROR')
        #   break cause error
        print('Details about operations')
        operations = ['READ', 'SUBMIT', 'UPDATE']
        while True:
            operation = self.clean_input(input('READ, UPDATE or SUBMIT ratings for movie "' + str(movie.capitalize()) + '"? '))
            if operation.upper() in operations:
                break
            else:
                print('Enter READ, UPDATE or SUBMIT\n')

        if operation == 'READ':
            # do you want to read all ratings for movie
            all = self.clean_input(input('Access all ratings or ratings for a particular user? Provide an ID or title: '))
            # if yes:
                # organise this here
        while True:
            user_ID = self.clean_input(input(operation.capitalize() + ' ratings for which user? Enter User ID: '))
            if user_ID:
                break
            else:
                print('User ID cannot be empty!')
        if operation == 'READ':
            # read all or for a specific client
            ['READ', ]
            pass
        else:
            while True:
                rating = self.clean_input(input('Enter a new rating: e.g. 3.0 '))
                if rating:
                    break
                else:
                    print('Rating cannot be empty!')
            if operation == 'SUBMIT':
                pass
            # do submit
            else:
                # assume update
                pass
                # do update



Client().main()
# connect to the front end down here

