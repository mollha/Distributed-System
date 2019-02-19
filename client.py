import Pyro4

uri = input("What is the Pyro uri of the Hello object? ").strip()
name = input("What is your name? ").strip()

Hello = Pyro4.Proxy(uri)
print("Response: ", Hello.say_hello(name))