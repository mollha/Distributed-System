import Pyro4


@Pyro4.expose
class Hello(object):
    def say_hello(self, name):
        return "Hello, {0}: " \
                "Successful remote invocation!".format(name)


daemon = Pyro4.Daemon()         # make a Pyro daemon
uri = daemon.register(Hello)       # reguest the Hello as a Pyro object

print("Server ready: object uri = ", uri)
daemon.requestLoop()                    # start the event loop of the server to wait for calls


# TODO consistency control - if asked to process a request that doesn't make sense then ask for updates first
