# Client.py

import Pyro4

uri = input("What is the Pyro uri of the Hello object? ").strip()
name = input("What is your name? ").strip()

Hello = Pyro4.Proxy(uri)        # get a Pyro proxy to the Hello object
print("Response: ", Hello.say_hello(name))      # call a remote method
