import uuid
from csv import reader
from random import choices
from datetime import datetime
import time
from Exceptions import *
import Pyro4


class Replica(object):
    def __init__(self):
        # The value of the application state as maintained by the RM. Each RM is a state machine, which begins with a
        # specified initial value and is thereafter solely the result of applying update operations to that state.
        self.movie_dict = read_database()
        self.name = 'replica_manager_' + str(uuid.uuid4())
        self.update_log = {}
        self.value_timestamp = [0, 0, 0]
        self.timestamp_table = {}



    def get_id(self, movie_identifier):
        movie_id = None
        try:
            movie_id = int(movie_identifier)
        except ValueError:
            # treat it as a string instead
            for ID, item in self.movie_dict.items():
                if movie_identifier.lower() == item[0].lower():
                    movie_id = ID
        return movie_id

    def get_movie(self, movie_identifier: str) -> list:
        movie_id = self.get_id(movie_identifier)
        try:
            return [movie_id] + self.movie_dict[movie_id]
        except KeyError:
            raise InvalidMovieError('"' + movie_identifier + '"' + ' is not a valid movie ID or title')

    @Pyro4.expose
    @property
    def get_status(self):
        return choices(population=['active', 'offline', 'over-loaded'], k=1, weights=[0.75, 0.05, 0.2])[0]

    @Pyro4.expose
    @property
    def get_replica_timestamp(self):
        return

    @Pyro4.expose
    def direct_request(self, request):
        operation = request[0]
        if operation in ['read', 'delete']:
            params = request[1:3]
        else:
            params = request[1:]
        return getattr(self, operation)(*params)

    @Pyro4.expose
    def gossip(self):
        # replica_manager.get_timestamp()
        return

    @Pyro4.expose
    def read(self, movie_identifier, user_ID):
        movie = self.get_movie(movie_identifier)
        ratings = movie[4]

        if ratings:
            total_rating = 0
            for rating in ratings:
                total_rating += float(rating[1])
            average_rating = round(total_rating / len(ratings), 1)

            for review in ratings:
                author = review[0]
                if user_ID == author:
                    return '\n--------- Movie Info ---------\n' + \
                        'ID:\t' + str(movie[0]) + '\n' + \
                        'Title:\t' + movie[1] + '\n' + \
                        'Year:\t' + movie[2] + '\n' + \
                        'Genres:\t' + ", ".join(movie[3]) + '\n' + \
                        'Average Rating: ' + str(average_rating) + '\n' + \
                        '\n----------- Rating -----------\n' + \
                        'Rating: ' + review[1] + '\n' + \
                        'Posted on ' + datetime.utcfromtimestamp(int(float(review[2]))).strftime('%d.%m.%Y') + \
                        ' by user "' + author + '"' + '\n'

            raise InvalidUserError('User "' + user_ID + '" has not submitted a review for movie "' + movie[1] + '"')
        else:
            raise InvalidMovieError('No ratings to show for movie "' + movie[1] + '"')

    @Pyro4.expose
    def update(self, movie_identifier, user_ID, rating):
        movie = self.get_movie(movie_identifier)
        ratings = movie[4]

        if len(ratings):
            rating_exists = False
            for review_no, review in enumerate(ratings):
                author = review[0]
                if user_ID == author:
                    self.movie_dict[movie[0]][3][review_no] = [user_ID, str(rating), str(time.time())]
                    rating_exists = True
                    self.timestamp += 1

            if not rating_exists:
                raise InvalidUserError('User "' + user_ID + '" has not submitted a review for movie "' + movie[1] + '"')
        else:
            raise InvalidMovieError('No ratings to show for movie "' + movie[1] + '"')

    @Pyro4.expose
    def submit(self, movie_identifier, user_ID, rating):
        movie = self.get_movie(movie_identifier)
        for review in movie[4]:
            author = review[0]
            if user_ID == author:
                raise InvalidUserError('User "' + user_ID + '" has already reviewed movie "' + movie[1] + '"')
        self.movie_dict[movie[0]][3].append([user_ID, str(rating), str(time.time())])
        self.timestamp += 1

    @Pyro4.expose
    def delete(self, movie_identifier, user_ID):
        movie = self.get_movie(movie_identifier)
        ratings = movie[4]

        if len(ratings):
            rating_exists = False
            for review_no, review in enumerate(ratings):
                author = review[0]
                if user_ID == author:
                    del self.movie_dict[movie[0]][3][review_no]
                    rating_exists = True

            if not rating_exists:
                raise InvalidUserError('User "' + user_ID + '" has not submitted a review for movie "' + movie[1] + '"')
        else:
            raise InvalidMovieError('No ratings to show for movie "' + movie[1] + '"')

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
                try:
                    year = str(int(year))
                except ValueError:
                    name = row[1]
                    year = '-'
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


if __name__ == '__main__':
    ns = Pyro4.locateNS()
    daemon = Pyro4.Daemon()
    replica = Replica()
    uri = daemon.register(replica)
    ns.register(replica.name, uri, safe=True)
    print('Starting ' + str(replica.name) + '...')

    daemon.requestLoop()
