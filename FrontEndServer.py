import Pyro4


class FrontEndServer(object):
    def __init__(self):
        self.replicas = []

    @Pyro4.expose
    def register_replica(self, ID):
        print("Registered " + str(ID))
        self.replicas.append(ID)

    @Pyro4.expose
    def request(self, request: list):
        print("Received request saying ...")
        try:
            replica_name = self.get_replica_name()
            with Pyro4.Proxy('PYRONAME:'+str(replica_name)) as replica:
                if request[0] == 'FIND':
                    return replica.get_info(request[1])
                elif request[0] == 'READ':
                    return replica.read(request[1], request[2])
                elif request[0] == 'SUBMIT':
                    return replica.submit(request[1], request[2], request[3], request[4])
                elif request[0] == 'UPDATE':
                    return replica.update(request[1], request[2], request[3], request[4])
        except ConnectionRefusedError:
            return "ERROR: All replicas offline"

    def get_replica_name(self):
        overloaded = None
        for replica in self.replicas:
            status = replica.get_status()
            if status == 'active':
                print("Using " + str(replica))
                return replica
            elif status == 'over-loaded':
                overloaded = replica
        if overloaded:
            print("Using " + str(overloaded))
            return overloaded
        raise ConnectionRefusedError


front_end_server = FrontEndServer()
front_end_server.name_server = Pyro4.locateNS()
daemon = Pyro4.Daemon()
uri = daemon.register(front_end_server)
front_end_server.name_server.register("front_end_server", uri, safe=True)
print('Starting front-end server...')
daemon.requestLoop()
