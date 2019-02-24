import Pyro4
from Pyro4 import naming
from server import Server


class FrontEndServer(object):
    def __init__(self):
        replicas = 1
        self.server_list = []
        ns = Pyro4.locateNS()
        daemon = Pyro4.Daemon()
        uri = daemon.register(self)
        ns.register("front_end_server", uri, safe=True)
        print(ns.list())
        for server_no in range(replicas):
            print('server no '+str(server_no))
            Server(server_no)
            self.server_list.append(Pyro4.Proxy("PYRONAME:replica_manager"+str(server_no)))
        ns = Pyro4.locateNS()
        print(ns.list())
        daemon.requestLoop()

    @Pyro4.expose
    def say_hello(self):
        return "hey"

    def interact(self):
        return "hi"

    @Pyro4.expose
    def add_replica_manager(self):
        pass

FrontEndServer()
# TODO rather than ask which servers are available - assume they are until they aren't
# Once they become available they can respond to the front end server

