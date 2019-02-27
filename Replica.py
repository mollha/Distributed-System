import Pyro4
import uuid
from csv import reader
from random import choice
from datetime import datetime
import time


@Pyro4.behavior(instance_mode="single")        # it is already this by default
class Replica(object):
    def __init__(self):
        self.movie_dict = read_database()
        self.name = 'replica_manager_' + str(uuid.uuid4())

    @Pyro4.expose
    @property
    def get_status(self):
        return choice(['active', 'offline', 'over-loaded'])

    @Pyro4.expose
    def average_rating(self, movie_ID):
        ratings = self.movie_dict[movie_ID][3]
        total_rating = 0
        for rating in ratings:
            total_rating += rating[1]
        return total_rating / len(ratings)

    def get_movie(self, movie_identifier):
        movie_ID = None
        try:
            movie_ID = int(movie_identifier)
        except ValueError:
            # treat it as a string instead
            for ID, item in self.movie_dict.items():
                if movie_identifier.lower() == item[0].lower():
                    movie_ID = ID
        try:
            return self.movie_dict[movie_ID]
        except KeyError:
            return 'ERROR: "' + movie_identifier + '"' + ' is not a valid ID or title'

    @Pyro4.expose
    def get_info(self, movie_ID):
        info = self.get_movie(movie_ID)
        if isinstance(info, list):
            return '--------- Movie Info ---------\n' +\
                   'ID:\t\t' + str(movie_ID) + '\n' +\
                   'Title:\t' + info[0] + '\n' +\
                   'Year:\t' + info[1] + '\n' +\
                   'Genres:\t' + ", ".join(info[2]) + '\n'
        else:
            return info

    # make sure user_ID comes through as a string
    @Pyro4.expose
    def read(self, movie_ID, user_ID=None):
        info = self.get_movie(movie_ID)
        if isinstance(info, list):
            if len(info):
                if user_ID:
                    desc = 'ERROR: user "' + user_ID + '" has not submitted a review for movie ' + movie_ID
                    for review in info[3]:
                        author = review[0]
                        if user_ID == author:
                            desc = '\nRating: ' + review[1] + '\n' + \
                                   'Posted on ' + datetime.utcfromtimestamp(int(review[2])).strftime('%d.%m.%Y') + \
                                   ' by user "' + author + '"' + '\n'
                else:
                    desc = ''
                    for review in info[3]:
                        desc += '\nRating: ' + review[1] + '\n' + \
                                'Posted on ' + datetime.utcfromtimestamp(int(review[2])).strftime('%d.%m.%Y') + \
                                ' by user "' + review[0] + '"' + '\n'
                return desc
            else:
                return 'No ratings to show for movie "' + movie_ID + '"'
        else:
            return info

    @Pyro4.expose
    def update(self, movie_ID, user_ID, rating):
        try:
            rating = float(rating)
            info = self.get_movie(movie_ID)
            if isinstance(info, list):
                if len(info):
                    desc = 'ERROR: User "' + user_ID + '" has not submitted a review for movie ' + movie_ID
                    for review in info[3]:
                        author = review[0]
                        if user_ID == author:
                            self.movie_dict[movie_ID] = [user_ID, str(rating), str(time.time())]
                            return 'SUCCESS: Dictionary successfully updated rating'
                    return desc
                else:
                    return 'No ratings to show for movie "' + movie_ID + '"'
            else:
                return info
        except ValueError:
            return 'ERROR: Rating "' + str(rating) + '" is not a number!'

    # only one review per film per user
    @Pyro4.expose
    def submit(self, movie_ID, user_ID, rating):
        try:
            rating = float(rating)
            if rating < 0 or rating > 5:
                return 'ERROR: Rating should be a number between 0 and 5!'
            info = self.get_movie(movie_ID)
            if isinstance(info, list):
                for review in info[3]:
                    author = review[0]
                    if user_ID == author:
                        return 'ERROR: User "' + user_ID + '" has already reviewed movie "' + movie_ID + '"'
                self.movie_dict[movie_ID] = [user_ID, str(rating), str(time.time())]
            else:
                return info
        except ValueError:
            return 'ERROR: Rating "' + str(rating) + '" is not a number!'


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
                # [user_ID, rating, time]
                movie_dict[int(row[1])][3].append([row[0], row[2], row[3]])
    return movie_dict


ns = Pyro4.locateNS()
daemon = Pyro4.Daemon()
replica = Replica()
uri = daemon.register(replica)
ns.register(replica.name, uri, safe=True)
print('Starting ' + str(replica.name) + '...')

with Pyro4.Proxy('PYRONAME:front_end_server') as front_end:
    front_end.register_replica(replica.name)

daemon.requestLoop()

# TODO consistency control - if asked to process a request that doesn't make sense then ask for updates first
