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
                movie_ID = row[0]
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
                movie_dict[row[1]][3].append([row[0], row[2], row[3]])

    return movie_dict


@Pyro4.expose
class Server(object):
    def __init__(self):
        self.status = 'active'
        self.movie_dict = read_database()

    def average_rating(self, movie_ID):
        ratings = self.movie_dict[movie_ID][3]
        total_rating = 0
        for rating in ratings:
            total_rating += rating[1]
        return total_rating / len(ratings)

    def update_status(self):
        self.status = choice(['active', 'offline', 'over-loaded'])


daemon = Pyro4.Daemon()         # make a Pyro daemon
uri = daemon.register(Server)   # reguest the Server as a Pyro object

print("Server ready: object uri = ", uri)
daemon.requestLoop()                    # start the event loop of the server to wait for calls


# TODO consistency control - if asked to process a request that doesn't make sense then ask for updates first
