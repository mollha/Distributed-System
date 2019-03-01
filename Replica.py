import Pyro4
import uuid
from csv import reader
from random import choices
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
        return choices(population=['active', 'offline', 'over-loaded'], k=1, weights=[0.75, 0.2, 0.05])[0]

    @Pyro4.expose
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
            return [movie_ID] + self.movie_dict[movie_ID]
        except KeyError:
            return 'ERROR: "' + movie_identifier + '"' + ' is not a valid ID or title'

    @Pyro4.expose
    def read(self, movie_ID, user_ID=None):
        movie = self.get_movie(movie_ID)
        if isinstance(movie, list):
            if len(movie):
                ratings = movie[4]
                total_rating = 0
                for rating in ratings:
                    total_rating += float(rating[1])
                average_rating = round(total_rating / len(ratings), 1)
                info = '\n--------- Movie Info ---------\n' +\
                       'ID\t\t' + str(movie[0]) +\
                       'Title:\t' + movie[1] + '\n' +\
                       'Year:\t' + movie[2] + '\n' +\
                       'Genres:\t' + ", ".join(movie[3]) + '\n' +\
                       'Average Rating: ' + str(average_rating) + '\n'

                if user_ID:
                    desc = 'ERROR: User "' + user_ID + '" has not submitted a review for movie ' + movie_ID
                    for review in ratings:
                        author = review[0]
                        if user_ID == author:
                            desc = info + '\nRating: ' + review[1] + '\n' + \
                                   'Posted on ' + datetime.utcfromtimestamp(int(review[2])).strftime('%d.%m.%Y') + \
                                   ' by user "' + author + '"' + '\n'
                else:
                    desc = info
                    for review in ratings:
                        desc += '\nRating: ' + review[1] + '\n' + \
                                'Posted on ' + datetime.utcfromtimestamp(int(review[2])).strftime('%d.%m.%Y') + \
                                ' by user "' + review[0] + '"' + '\n'
                return desc
            else:
                return 'No ratings to show for movie "' + movie_ID + '"'
        else:
            return movie

    @Pyro4.expose
    def update(self, movie_ID, user_ID, rating):
        movie = self.get_movie(movie_ID)
        if isinstance(movie, list):
            if len(movie):
                desc = 'ERROR: User "' + user_ID + '" has not submitted a review for movie ' + movie_ID
                for review in movie[4]:
                    author = review[0]
                    if user_ID == author:
                        self.movie_dict[movie_ID] = [user_ID, str(rating), str(time.time())]
                        return 'SUCCESS: Dictionary successfully updated rating'
                return desc
            else:
                return 'No ratings to show for movie "' + movie_ID + '"'
        else:
            return movie

    # only one review per film per user
    @Pyro4.expose
    def submit(self, movie_ID, user_ID, rating):
        movie = self.get_movie(movie_ID)
        if isinstance(movie, list):
            for review in movie[4]:
                author = review[0]
                if user_ID == author:
                    return 'ERROR: User "' + user_ID + '" has already reviewed movie "' + movie_ID + '"'
            self.movie_dict[movie_ID][3].append([user_ID, str(rating), str(time.time())])
            return 'SUCCESS: Dictionary successfully submitted rating'
        else:
            return movie

    @Pyro4.expose
    def delete(self, movie_ID, user_ID=None):
        movie = self.get_movie(movie_ID)
        if isinstance(movie, list):
            if len(movie):
                desc = 'ERROR: User "' + user_ID + '" has not submitted a review for movie ' + movie_ID
                for review in movie[4]:
                    author = review[0]
                    if user_ID == author:
                        desc = 'SUCCESS: Rating removed successfully'
                return desc
            else:
                return 'No ratings to show for movie "' + movie_ID + '"'
        else:
            return movie

# piece of gossip - you can share it
# if you dont have it you cant request for it
# replica manager should update itself before giving updates
# ask one replica manager first, if it is down, try a new one
# only stop using it once it is down
# if normal replica manager is overloaded, try 2 and it has an update,
# download and send to client so FE knows theres more up to date information
# only change replica if their usual is overloaded
# ONLY PERMANENTTLY SWITCH IF THE SERVER IS OFFLINE!!!
# IF SERVER IS OVERLOADED THEN MOVE TO THE NEXT TEMPORARILY


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

# check if front end actually on
with Pyro4.Proxy('PYRONAME:front_end_server') as front_end:
    front_end.register_replica(replica.name)

daemon.requestLoop()

# TODO consistency control - if asked to process a request that doesn't make sense then ask for updates first
