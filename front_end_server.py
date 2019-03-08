from typing import Union
import Pyro4
# This import statement is required as the front-end server
# may need to pass these exceptions to the client
from exceptions import InvalidUserError, InvalidMovieError


class FrontEndServer(object):
    def __init__(self):
        self.replicas = {}
        self.replica_id = -1
        self.default_replica = 0
        self.prev = [0, 0, 0]
        self.update_id = 0

    @Pyro4.expose
    def register_replica(self, replica_name: str, replica: Pyro4.Proxy) -> int:
        """
            Each replica separately calls this method to register itself with the front-end
            This is faster than if the front-end had to look up each replica individually
            :param replica: A Pyro4.Proxy of the replica to be registered
            :param replica_name: A string containing the name of the replica to be registered
            :return: An integer, replica_id
        """
        self.replica_id += 1
        self.replicas[self.replica_id] = replica
        print("Registered %s" % str(replica_name))
        return self.replica_id

    @Pyro4.expose
    def forward_request(self, client_request: list) -> Union[Exception, str]:
        """
            The front-end server forwards a request to an active replica
            If there are no active replicas it will try again
            :param client_request: A list containing the request from the client
            :return: An exception or a string is returned
        """
        try:
            replica = self.get_replica()
            operation = client_request[0]
            print('\nReceived request to %s' % operation, '"%s" rating' % client_request[1],
                  'for user %s' % client_request[2])
            replica.gossip_request(self.prev)
            response = replica.process_request(client_request, self.update_id)
            if not isinstance(response, Exception):
                self.prev = [max(self.prev[index], response[0][index])
                             for index in range(len(self.replicas))]
                return response[1]
            # response is an error therefore doesn't contain a timestamp
            return response
        except ConnectionRefusedError as error_message:
            print(error_message)
            print('Reconnecting...\n')
            self.forward_request(client_request)

    @Pyro4.expose
    def send_other_replicas(self, exclude_id):
        other_replicas = {}
        for replica_id, replica in self.replicas.items():
            if replica_id == exclude_id:
                continue
            other_replicas[replica_id] = replica
        return other_replicas

    def get_replica(self) -> Pyro4.Proxy:
        """
            If the default replica becomes overloaded - search for another replica
            that is active and use this until the default replica becomes available
            If the default replica has failed then search for an active replica to
            make this the new default replica
            If there are no active replicas, make an overloaded replica the new default
            If all replicas are offline, raise a ConnectionRefusedError
            :return: A Pyro4.Proxy of a replica
        """
        # sometimes a key error
        replica = self.replicas[self.default_replica]
        status = replica.get_status()
        if status == 'active':
            return replica
        overloaded = None
        registered_replicas = len(self.replicas)
        for new_replica_pos in range(self.default_replica + 1, self.default_replica + registered_replicas):
            new_replica = self.replicas[new_replica_pos % registered_replicas]
            new_status = replica.get_status()
            if new_status == 'active':
                if status == 'offline':
                    self.default_replica = new_replica_pos
                return new_replica
            if new_status == 'overloaded':
                overloaded = new_replica
        if status == 'overloaded':
            return replica
        if overloaded:
            return overloaded
        raise ConnectionRefusedError('ERROR: All replicas offline')

# except Exception as error:
        #     print(type(error))
        #     print('ERROR: %s' % error)
        #     return


if __name__ == '__main__':
    print('Starting front-end server...')
    FRONT_END_SERVER = FrontEndServer()
    NS = Pyro4.locateNS()
    DAEMON = Pyro4.Daemon()
    URI = DAEMON.register(FRONT_END_SERVER)
    NS.register("front_end_server", URI, safe=True)
    print('Ready to receive requests\n')
    DAEMON.requestLoop()
