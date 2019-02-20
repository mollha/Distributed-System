import Pyro4


@Pyro4.expose
class Hello(object):
    def say_hello(self, name):
        return "Hello, {0}: " \
                "Successful remote invocation!".format(name)


daemon = Pyro4.Daemon()         # make a Pyro daemon
uri = daemon.register(Hello)       # reguster the Hello as a Pyro object

print("Server ready: object uri = ", uri)
daemon.requestLoop()                    # start the event loop of the server to wait for calls
