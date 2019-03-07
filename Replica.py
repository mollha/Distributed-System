import uuid
from csv import reader
from random import choices
from datetime import datetime
import time
import Pyro4
from Exceptions import *


class Replica(object):
    def __init__(self):
        self.movie_dict = read_database()
        self.other_replicas = {}
        self.name = 'replica_manager_' + str(uuid.uuid4())
        self.update_log = {}
        self.value_timestamp = [0, 0, 0]
        self.timestamp_table = {}
        self.replica_id = None


    # TODO - need to create a way to list the other proxies

    @Pyro4.expose
    def get_status(self):
        """
            Randomly generates a status for this RM
            This is weighted in favour of active (p = 0.75) and overloaded (p = 0.2)
            :return: A string denoting the status of this RM
        """
        return choices(population=['active', 'offline', 'over-loaded'], k=1, weights=[0.7, 0.1, 0.2])[0]

    def get_movie_id(self, movie_identifier: str) -> int:
        """
            If the movie_identifier can be transformed to an int without throwing a ValueError,
            then movie_identifier is already an ID
            Alternatively, if the movie_identifier throws a ValueError - it is assumed that the
            movie_identifier represents a movie title instead for which the movie ID is found
            :param movie_identifier: A string containing either a movie title or movie ID
            :return: An integer, movie ID
        """
        movie_id = None
        try:
            movie_id = int(movie_identifier)
        except ValueError:
            for ID, item in self.movie_dict.items():
                if movie_identifier.lower() == item[0].lower():
                    movie_id = ID
        return movie_id

    def get_movie(self, movie_identifier: str) -> list:
        """
            Given a movie_identifier (ID or title), retrieve the movie from the database
            :param movie_identifier: A string containing either a movie title or movie ID
            :return: A list containing the movie_id its database entry
        """
        movie_id = self.get_movie_id(movie_identifier)
        try:
            return [movie_id] + self.movie_dict[movie_id]
        except KeyError:
            raise InvalidMovieError('"' + movie_identifier + '"' + ' is not a valid movie ID or title')

    @Pyro4.expose
    def direct_request(self, fe_prev: list, request: list, update_id: int = None):
        if self.already_processed(update_id):
            return
        # self.gossip(fe_prev)
        # applies updates - applies no updates if the timestamps are the same
        # assume that replica is up to date
        # this is why we only need update log and not executed too - theyre the same
        # first check if the update has been seen before
        operation = request[0]
        if operation in ['read', 'delete']:
            params = request[1:3]
        else:
            params = request[1:]
        response = getattr(self, operation)(*params)
        # if we got that the update went through as expected
        print('self value 1', self.value_timestamp)
        if isinstance(response, Exception) and id:
            # update value timestamp
            self.value_timestamp[self.replica_id] += 1
            self.update_log[update_id] = (self.value_timestamp, request)

        print('self value 2', self.value_timestamp)
        print('fe_prev timestamp', fe_prev)
        return self.value_timestamp, response

        #return timestamp then response only for non errors
        # [self.prev, client_request, self.update_id]

    def already_processed(self, update_id):
        try:
            self.update_log[update_id]
            return True
        except KeyError:
            return False

    @Pyro4.expose
    def gossip(self, fe_prev):
        # replica_list = self.name_server.list('replica_manager_')
        # not right, this must be  <= not just > or <
        updates_required = [replica_list[index] for index in range(len(replica_list)) if fe_prev[index] < self.value_timestamp[index]]

        for replica_with_update in updates_required:
            with Pyro4.Proxy('PYRONAME:%s' % replica_with_update) as RM:
                # apply the updates from other replicas
                # value_timestamp will update itself
                response = RM.respond(self.update_log, self.value_timestamp)
                for update_id, update in response:
                    if not self.already_processed(update_id):
                        # apply updates and add them to the log
                        pass
                return

    def respond(self, update_log, timestamp):
        response = {}
        for update_id, entry in update_log:
            if entry[0][self.replica_id] > timestamp[self.replica_id]:
                response[update_id] = entry
        return response

    # im not going to clear the log

    # ------------- QUERY METHOD -------------
    @Pyro4.expose
    def read(self, movie_identifier: str, user_id: str) -> str:
        """
            Given a movie_identifier (ID or title) and a user id
            Retrieve this rating from the database and present it as a well-formatted string
            :param movie_identifier: A string containing either a movie title or movie ID
            :param user_id: A string containing a user_id
            :return: A list containing the movie_id and its database entry
        """
        movie = self.get_movie(movie_identifier)
        ratings = movie[4]

        if ratings:
            total_rating = 0
            for rating in ratings:
                total_rating += float(rating[1])
            average_rating = round(total_rating / len(ratings), 1)

            for review in ratings:
                author = review[0]
                if user_id == author:
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

            raise InvalidUserError('User "' + user_id + '" has not submitted a review for movie "' + movie[1] + '"')
        else:
            raise InvalidMovieError('No ratings to show for movie "' + movie[1] + '"')

    # ------------- UPDATE METHODS -------------
    @Pyro4.expose
    def delete(self, movie_identifier: str, user_id: str) -> None:
        """
            Given a movie_identifier (ID or title) and a user id
            Delete the corresponding rating from the database (if it exists)
            :param movie_identifier: A string containing either a movie title or movie ID
            :param user_id: A string containing a user_id
        """
        movie = self.get_movie(movie_identifier)
        ratings = movie[4]

        if ratings:
            rating_exists = False
            for review_no, review in enumerate(ratings):
                author = review[0]
                if user_id == author:
                    del self.movie_dict[movie[0]][3][review_no]
                    rating_exists = True

            if not rating_exists:
                raise InvalidUserError('User "' + user_id + '" has not submitted a review for movie "' + movie[1] + '"')
        else:
            raise InvalidMovieError('No ratings to show for movie "' + movie[1] + '"')

    @Pyro4.expose
    def update(self, movie_identifier: str, user_id: str, rating: float) -> None:
        """
            Given a movie_identifier (ID or title), user id and rating
            Update the corresponding rating in the database (if it exists)
            :param movie_identifier: A string containing either a movie title or movie ID
            :param user_id: A string containing a user_id
            :param rating: A float representing a movie rating
        """
        movie = self.get_movie(movie_identifier)
        ratings = movie[4]

        if ratings:
            rating_exists = False
            for review_no, review in enumerate(ratings):
                author = review[0]
                if user_id == author:
                    self.movie_dict[movie[0]][3][review_no] = [user_id, str(rating), str(time.time())]
                    rating_exists = True

            if not rating_exists:
                raise InvalidUserError('User "' + user_id + '" has not submitted a review for movie "' + movie[1] + '"')
        else:
            raise InvalidMovieError('No ratings to show for movie "' + movie[1] + '"')

    @Pyro4.expose
    def submit(self, movie_identifier, user_id, rating) -> None:
        movie = self.get_movie(movie_identifier)
        for review in movie[4]:
            author = review[0]
            if user_id == author:
                raise InvalidUserError('User "' + user_id + '" has already reviewed movie "' + movie[1] + '"')
        self.movie_dict[movie[0]][3].append([user_id, str(rating), str(time.time())])


# ---------- READING MOVIE AND RATINGS INFO INTO THE DATABASE ----------
# [[name], year, [genres], [ratings]]
def read_database():
    movie_dict = {}
    with open('data/movies.csv', encoding='utf-8') as movie_data:
        movie_reader = reader(movie_data, delimiter=',')
        skip_row = True
        for row in movie_reader:
            if skip_row:
                skip_row = False
            else:
                id_movie = int(row[0])
                name = row[1][:-7]
                year = row[1][-5:-1]
                try:
                    year = str(int(year))
                except ValueError:
                    name = row[1]
                    year = '-'
                genres = row[2].split('|')
                movie_dict[id_movie] = [name, year, genres, []]

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
    REPLICA = Replica()
    print('Starting ' + str(REPLICA.name) + '...')
    NS = Pyro4.locateNS()
    DAEMON = Pyro4.Daemon()
    URI = DAEMON.register(REPLICA)
    NS.register(REPLICA.name, URI, safe=True)
    print('Connecting ' + str(REPLICA.name) + ' to front-end server ...')

    # Replica connects to the front-end server and passes a proxy of itself to the front-end
    with Pyro4.Proxy('PYRONAME:front_end_server') as front_end_server:
        REPLICA.replica_id = front_end_server.register_replica(REPLICA.name, REPLICA)
        print(REPLICA.replica_id)

    print("Ready to receive requests\n")
    DAEMON.requestLoop()
