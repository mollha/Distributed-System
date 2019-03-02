import Pyro4
import time
from Exceptions import InvalidInputError


class FrontEndServer(object):
    def __init__(self):
        self.replicas = []
        self.current_replica = 0

    @Pyro4.expose
    def register_replica(self, replica_name):
        s1 = time.time()
        replica = Pyro4.Proxy('PYRONAME:' + replica_name)
        self.replicas.append(replica)
        print("Registered %s" % str(replica_name))
        print('time', str(time.time() - s1))

    @Pyro4.expose
    def direct_request(self, request):
        try:
            operation = request[0]
            print("Received request to %s" % operation.lower(), " ")
            s1 = time.time()
            replica = self.get_replica()
            print(time.time() - s1)
            if operation == 'READ':
                return replica.read(request[1], request[2])
            elif operation == 'DELETE':
                return replica.delete(request[1], request[2])
            elif operation == 'SUBMIT':
                return replica.submit(request[1], request[2], request[3])
            elif operation == 'UPDATE':
                return replica.update(request[1], request[2], request[3])
        except ConnectionRefusedError:
            return "ERROR: All replicas offline"
        # except InvalidInputError as e:
        #     print(e)

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
