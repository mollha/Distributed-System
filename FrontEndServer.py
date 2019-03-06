import Pyro4

# fault_tolerance = 2 (f-1)


class FrontEndServer(object):
    def __init__(self):
        self.replicas = {}
        self.current_replica = 0
        self.prev = []
        self.update_id = 0

    # send to multiple replica managers
    @Pyro4.expose
    def forward_request(self, client_request):
        # need to send prev too with updates only
        # this should receive the new vector timestamp
        try:
            operation = client_request[0]
            print('Received request to %s' % operation, '"%s" rating' % client_request[1], 'for user %s' % client_request[2])
            replica = self.get_replica()
            self.update_id += 1
            response = replica.direct_request(self.prev, client_request, self.update_id)

            # send it to 1 rm
            # if this update is successful then we can send it to the other 2 without returning anything

            if type(response) != Exception:
                # merge
                self.prev = [max(self.prev[index], response[0][index]) for index in range(len(self.replicas))]
                return response[1]
            return response  # receive error response only - no timestamp
        except ConnectionRefusedError:
            return "ERROR: All replicas offline"

    # TODO rework this section
    # rework it so that the request can be sent to all that are online
    # if this makes sense in terms of gossip

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
    print('Starting front-end server...')
    front_end_server = FrontEndServer()
    ns = Pyro4.locateNS()
    daemon = Pyro4.Daemon()
    uri = daemon.register(front_end_server)
    ns.register("front_end_server", uri, safe=True)

    for replica_no, replica_name in enumerate(ns.list('replica_manager_')):
        replica_manager = Pyro4.Proxy('PYRONAME:' + replica_name)
        replica_manager.set_id(replica_no)
        front_end_server.replicas[replica_name] = replica_manager
        front_end_server.prev.append(0)
        print("Registered %s" % str(replica_name))


    daemon.requestLoop()
