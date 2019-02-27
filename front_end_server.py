import Pyro4


class FrontEndServer(object):
    def __init__(self):
        self.replicas = []

    def request(self):
        pass

    def get_replica(self):
        overloaded = None
        for replica in self.replicas:
            status = replica.get_status()
            if status == 'active':
                return replica
            if status == 'over-loaded':
                overloaded = replica
        if not overloaded:
            return 'No servers online'
        else:
            # use an overloaded server if you have to
            return overloaded


    @Pyro4.expose
    def register_replica(self, ID):
        print("Registered " + str(ID))
        self.replicas.append(ID)


front_end_server = FrontEndServer()
front_end_server.name_server = Pyro4.locateNS()
daemon = Pyro4.Daemon()
uri = daemon.register(front_end_server)
front_end_server.name_server.register("front_end_server", uri, safe=True)
print('Starting front-end server...')
daemon.requestLoop()

# Once a client connects, Pyro will create an instance of the class and use that single object to handle the remote method calls during one client proxy session.