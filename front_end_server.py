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

    def clean_input(self):
        # client should do this
        # check input not empty
        # m
        pass

    @Pyro4.expose
    def interact_1(self):
        return "hey"

    def interact(self):
        for server in self.server_list:
            if server.get_status != 'active':
                continue

    @Pyro4.expose
    def add_replica_manager(self):
        pass

    @Pyro4.expose
    def receive_id_or_title(self):


FrontEndServer()
# TODO rather than ask which servers are available - assume they are until they aren't
# Once they become available they can respond to the front end server


daemon = Pyro4.Daemon()
uri = daemon.register(MyPyroThing) # need to reister the front end server here otherwisee this wont come onto the original message??
print(uri)
daemon.requestLoop()

# Once a client connects, Pyro will create an instance of the class and use that single object to handle the remote method calls during one client proxy session.