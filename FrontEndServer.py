import Pyro4
import time
from Exceptions import *

# fault_tolerance = 2 (f-1)
class FrontEndServer(object):
    def __init__(self):
        # name server registered here
        self.prev = [0, 0, 0]# empty timestamp
        self.replicas = []
        self.current_replica = 0

    @Pyro4.expose
    def register_replica(self, replica_name):
        replica = Pyro4.Proxy('PYRONAME:' + replica_name)
        self.replicas.append(replica)
        print("Registered %s" % str(replica_name))

    @Pyro4.expose
    def forward_request(self, request):
        # need to send prev too with updates only
        try:
            print('Received request to %s' % request[0].lower(), '"%s" rating' % request[1], 'for user %s' % request[2])
            s1 = time.time()
            replica = self.get_replica()
            print(time.time() - s1)
            return replica.direct_request(request)
        except ConnectionRefusedError:
            return "ERROR: All replicas offline"

    def get_replica(self):
        replica = self.replicas[self.current_replica]
        status = replica.get_status
        print(status)
        if status == 'active':
            return replica
        elif status == 'over-loaded':
            server = None
            server_no = self.current_replica
            while not server:
                server_no += self.current_replica
                replica = self.replicas[server_no]
                status = replica.get_status
                if status == 'active':
                    return replica
                raise ConnectionRefusedError
        elif status == 'offline':
            self.current_replica = (self.current_replica + 1) % 3
            return self.get_replica()

        print(len(self.replicas), self.replicas)


if __name__ == '__main__':
    front_end_server = FrontEndServer()
    front_end_server.name_server = Pyro4.locateNS()
    daemon = Pyro4.Daemon()
    uri = daemon.register(front_end_server)
    front_end_server.name_server.register("front_end_server", uri, safe=True)
    print('Starting front-end server...')
    daemon.requestLoop()
