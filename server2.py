import Pyro4
import read_update_csv as data
import sys

status = "online"

rating_dict = data.movie_rating_dict
id_dict = data.movie_id_dict

# retrieve, submit and update movie ratings


class Database:
    status = "Active"
    counter = 0

    def update_movie_rating(self, movie, id):
        #TODO updates movie rating
        return

    def get_movie_rating(self, movie):
        #TODO return movie rating for given film
        return

    def go_offline(self):
        Database.status = "Offline"

    def overload(self):
        Database.status = "Overload"

    def online(self):
        Database.status = "Online"

    def increment_counter(self):
        Database.counter += 1





def update_status():
    pass


daemon = Pyro4.Daemon()
uri = daemon.register(Database)

with Pyro4.locateNS() as name_server:
    name_server.register("ratings.database." + str(uri), uri, safe=True)


print("Server Ready: Object URI = " + str(uri))
sys.excepthook = Pyro4.util.excepthook
daemon.requestLoop()