# Client.py

import Pyro4

# set up a connection
server = Pyro4.Proxy("PYRONAME:front_end_server")    # use name server object lookup uri shortcut


# connect to the front end




print(server.say_hello())

while True:
    validInput = False  # initially, valid input is false
    while not validInput:  # while the input is not valid
        inputString = input('Input artist name or "quit" to disconnect: ')  # receive input
        inputString = inputString.strip('"'"'"' ').lower()  # strips leading and trailing whitespace and commas
        while '  ' in inputString:  # while there are double whitespaces within artist name
            inputString = inputString.replace('  ', ' ')  # replace them with a single whitespace
        if inputString != "":  # if the input is not empty after string is cleaned, this is considered valid
            validInput = True  # input is considered valid
        else:  # otherwise
            print('Empty input is not valid - input alphanumeric characters')