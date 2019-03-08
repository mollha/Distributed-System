import uuid
from csv import reader
from random import choices
from datetime import datetime
import time
import Pyro4
from exceptions import *


class Replica(object):
    # To get the name of replicas during gossiping
    @Pyro4.expose
    @property
    def get_name(self):
        return self.name

    def __init__(self):
        self.movie_dict = read_database()
        self.other_replicas = {}
        self.name = 'replica_manager_' + str(uuid.uuid4())
        self.update_log = {}
        self.value_timestamp = [0, 0, 0]
        self.timestamp_table = {}
        self.replica_id = None

    @Pyro4.expose
    def get_status(self) -> str:
        """
            Randomly generates a status for this RM
            This is weighted in favour of active (p = 0.75), then over-loaded (p = 0.2),
            then offline (p = 0.05)
            :return: A string denoting the status of this RM
        """
        return choices(population=['active', 'offline', 'over-loaded'],
                       k=1, weights=[0.75, 0.05, 0.2])[0]

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
            for new_id, item in self.movie_dict.items():
                if movie_identifier.lower() == item[0].lower():
                    movie_id = new_id
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
            raise InvalidMovieError('"' + movie_identifier +
                                    '"' + ' is not a valid movie ID or title')

    @Pyro4.expose
    def process_request(self, request: list, update_id: int = None) -> tuple:
        """
        Directs the request to the correct method
        Adds updates to the update log and sets the new value of the replicas timestamp
        :param request: A list containing an operation, a movie_id, a user_id and a rating
        :param update_id: The id provided by the front-end representing an update
        :return: The current timestamp of this replica and the response to the request
        """
        operation = request[0]
        # If the request is a query or an update that has not been applied
        if operation == 'read' or update_id not in self.update_log.keys():
            operation = request[0]
            print('\nProcessing request to %s' % operation, '"%s" rating' % request[1],
                  'for user %s' % request[2])
            if operation in ['read', 'delete']:
                params = request[1:3]
            else:
                params = request[1:]

            # send the request to the relevant method and store the response
            response = getattr(self, operation)(*params)

            # If the update went through as expected
            # add the update to the update log and increment timestamp
            if not isinstance(response, Exception) and operation != 'read':
                self.value_timestamp[self.replica_id] += 1
                self.update_log[update_id] = (self.value_timestamp[:], request)
            return self.value_timestamp, response

    @Pyro4.expose
    def gossip_request(self, fe_prev: list) -> None:
        """
        Requests updates from other replicas with unseen updates
        :param fe_prev: The front-ends timestamp
        """
        # checks that the list of other replicas is empty before adding to it
        if not self.other_replicas:
            self.other_replicas = front_end_server.send_other_replicas(self.replica_id)
            for replica_id in self.other_replicas.keys():
                self.timestamp_table[replica_id] = [0, 0, 0]

        # compiles a list of the replicas that contain unseen updates
        updates_required = [(replica_id, self.other_replicas[replica_id])
                            for replica_id in self.other_replicas.keys()
                            if fe_prev[replica_id] > self.value_timestamp[replica_id]]

        # apply the updates from other replicas
        if updates_required:
            for replica_info in updates_required:
                print('Gossiping with', replica_info[1].get_name)
                response = replica_info[1].gossip_response(self.value_timestamp)
                self.timestamp_table[replica_info[0]] = response[0]

                # response[0] is the new timestamp for id
                for update_id, update in response[1].items():
                    # try and apply these updates
                    try:
                        self.process_request(update[1], update_id)
                    except InvalidUserError:
                        # can no longer apply this update because
                        # the replica has updated in the mean time
                        continue

        # clear the update log of updates that have been seen by all replicas
        clear = min([timestamp[self.replica_id] for timestamp in self.timestamp_table.values()])
        for update_id, update in self.update_log.items():
            if clear >= update[0][self.replica_id]:
                del self.update_log[update_id]

    @Pyro4.expose
    def gossip_response(self, timestamp: list) -> tuple:
        missing_updates = {}
        # iterate through update log and return the relevant updates
        for update_id, update_tuple in self.update_log.items():
            if update_tuple[0][self.replica_id] > timestamp[self.replica_id]:
                missing_updates[update_id] = update_tuple
        # also return this replicas timestamp so the other replica knows what this replicas has seen
        return self.value_timestamp, missing_updates

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

            raise InvalidUserError('User "' + user_id +
                                   '" has not submitted a review for movie "' + movie[1] + '"')
        else:
            raise InvalidMovieError('No ratings to show for movie "'
                                    + movie[1] + '"')

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
        print(movie[0])
        ratings = movie[4]

        if ratings:
            rating_exists = False
            for review_no, review in enumerate(ratings):
                author = review[0]
                if user_id == author:
                    del self.movie_dict[movie[0]][3][review_no]
                    rating_exists = True

            if not rating_exists:
                raise InvalidUserError('User "' + user_id +
                                       '" has not submitted a review for movie "' + movie[1] + '"')
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
                    self.movie_dict[movie[0]][3][review_no] = \
                        [user_id, str(rating), str(time.time())]
                    rating_exists = True

            if not rating_exists:
                raise InvalidUserError('User "' + user_id +
                                       '" has not submitted a review for movie "' + movie[1] + '"')
        else:
            raise InvalidMovieError('No ratings to show for movie "' + movie[1] + '"')

    @Pyro4.expose
    def submit(self, movie_identifier, user_id, rating) -> None:
        """
            Given a movie_identifier (ID or title), user id and rating
            Submit a new rating to the database (if it doesn't already exist)
            :param movie_identifier: A string containing either a movie title or movie ID
            :param user_id: A string containing a user_id
            :param rating: A float representing a movie rating
        """
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


# ------------ STARTING THE REPLICA --------------
if __name__ == '__main__':
    REPLICA = Replica()
    print('Starting ' + str(REPLICA.name) + '...')
    NS = Pyro4.locateNS()
    DAEMON = Pyro4.Daemon()
    URI = DAEMON.register(REPLICA)
    NS.register(REPLICA.name, URI, safe=True)
    print('Connecting ' + str(REPLICA.name) + ' to the front-end server ...')

    # Replica connects to the front-end server and passes a proxy of itself to the front-end
    with Pyro4.Proxy('PYRONAME:front_end_server') as front_end_server:
        REPLICA.replica_id = front_end_server.register_replica(REPLICA.name, REPLICA)

    print("Ready to receive requests\n")
    DAEMON.requestLoop()
