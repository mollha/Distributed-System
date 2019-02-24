import Pyro4
from csv import reader
from random import choice


def read_database():
    movie_dict = {}
    with open('data/movies.csv', encoding='utf-8') as movie_data:
        movie_reader = reader(movie_data, delimiter=',')
        skip_row = True
        for row in movie_reader:
            if skip_row:
                skip_row = False
            else:
                movie_ID = int(row[0])
                # parse year and name
                # [[names], year, [genres]]
                name = row[1][:-7]
                year = row[1][-5:-1]
                genres = row[2].split('|')
                movie_dict[movie_ID] = [name, year, genres, []]

    with open('data/ratings.csv', encoding='utf-8') as ratings_data:
        ratings_reader = reader(ratings_data, delimiter=',')
        skip_row = True
        for row in ratings_reader:
            if skip_row:
                skip_row = False
            else:
                movie_dict[int(row[1])][3].append([row[0], row[2], row[3]])

    return movie_dict


@Pyro4.behavior(instance_mode="single")        # it is already this by default
class Server(object):
    def __init__(self, server_no):
        self.status = 'active'
        self.movie_dict = read_database()
        # ns = Pyro4.locateNS()
        # print('hayyy')
        # daemon = Pyro4.Daemon()
        # uri = daemon.register(self)
        # ns.register("replica_manager"+str(server_no), uri, safe=True)
        # print(ns.list())
        # daemon.requestLoop()

    @Pyro4.oneway
    def update_status(self, status=None):
        status_list = ['active', 'offline', 'over-loaded']
        if status not in status_list:
            self.status = choice(status_list)
        else:
            self.status = status


    @Pyro4.expose
    def get_status(self):
        return self.status

    @Pyro4.expose
    def average_rating(self, movie_ID):
        ratings = self.movie_dict[movie_ID][3]
        total_rating = 0
        for rating in ratings:
            total_rating += rating[1]
        return total_rating / len(ratings)

    @Pyro4.expose
    def read(self, movie_ID):
        try:
            movie_ID = int(movie_ID)
            movie_info = self.movie_dict[movie_ID]
            print(movie_info)
            movie_name = movie_info[0]
            movie_release = movie_info[1]
            movie_genres = ",".join(movie_info[2])

        except ValueError:
            return 'ERROR: Movie ID "' + str(movie_ID) + '"' ' is not a number!'
        except KeyError:
            return 'ERROR: "' + str(movie_ID) + '"' + ' is not a valid Movie ID'



server = Server(5)
server.read('30a7')

# TODO consistency control - if asked to process a request that doesn't make sense then ask for updates first
