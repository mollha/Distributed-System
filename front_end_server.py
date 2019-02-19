import Pyro4


with Pyro4.locateNS() as name_server:
    server_dict = name_server.list(prefix="ratings.database.")



num_servers = len(server_dict.keys())

servers = server_dict.values()
server_list = []
def create_servers(server_dict):

for item in server_dict.values():
    server = Pyro4.Proxy(item)
    server_list.append(server)
