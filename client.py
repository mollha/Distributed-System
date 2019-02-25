# Client.py

import Pyro4

# set up a connection
# server = Pyro4.Proxy("PYRONAME:front_end_server")    # use name server object lookup uri shortcut


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
        # validate name and check user_ID doesn't already exist

    def clean_input(self, input_string):
        input_string = input_string.strip('"'"'"' ')  # strips leading and trailing whitespace and commas
        while '  ' in input_string:  # while there are double whitespaces within artist name
            input_string = input_string.replace('  ', ' ')  # replace them with a single whitespace
        return input_string



Client()

# while True:
#     validInput = False  # initially, valid input is false
#     while not validInput:  # while the input is not valid
#         inputString = input('Input artist name or "quit" to disconnect: ')  # receive input
#
#         if inputString != "":  # if the input is not empty after string is cleaned, this is considered valid
#             validInput = True  # input is considered valid
#         else:  # otherwise
#             print('Empty input is not valid - input alphanumeric characters')


