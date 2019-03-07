import uuid
from csv import reader
from random import choices
from datetime import datetime
import time
from Exceptions import *
import Pyro4


class Replica(object):
    # Accessor methods

    def __init__(self):
        # The value of the application state as maintained by the RM. Each RM is a state machine, which begins with a
        # specified initial value and is thereafter solely the result of applying update operations to that state.
        self.movie_dict = read_database()
        self.other_replicas = {}
        self.name = 'replica_manager_' + str(uuid.uuid4())
        self.update_log = {}
        # The Pyro name server. Storing it locally removes the overhead of re-locating it every time this RM gets
        # replicas_with_updates.
        self.ns = Pyro4.locateNS()
        self.value_timestamp = [0, 0, 0]
        self.timestamp_table = {}
        self.replica_id = None

    # TODO - need to create a way to list the other proxies

    @Pyro4.expose
    def get_status(self):
        return choices(population=['active', 'offline', 'over-loaded'], k=1, weights=[0.75, 0.05, 0.2])[0]

    @Pyro4.expose
    @Pyro4.oneway
    def set_id(self, new_id):
        self.replica_id = new_id

    def get_movie_id(self, movie_identifier):
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
        movie_id = self.get_movie_id(movie_identifier)
        try:
            return [movie_id] + self.movie_dict[movie_id]
        except KeyError:
            raise InvalidMovieError('"' + movie_identifier + '"' + ' is not a valid movie ID or title')


    @Pyro4.expose
    def direct_request(self, fe_prev, request, update_id=None):
        print('got her')
        if self.already_processed(update_id):
            print('ok')
            return
        print('here')
        self.gossip(fe_prev)
        print('got here')
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
        if type(response) != Exception and id:
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
        replica_list = self.ns.list('replica_manager_')
        # not right, this must be  <= not just > or <
        updates_required = [replica_list[index] for index in range(len(replica_list)) if fe_prev[index] < self.value_timestamp[index]]

        for replica_with_update in updates_required:
            with Pyro4.Proxy('PYRONAME:%s' % replica_with_update) as rm:
                # apply the updates from other replicas
                # value_timestamp will update itself
                response = rm.respond(self.update_log, self.value_timestamp)
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

    with Pyro4.Proxy('PYRONAME:front_end_server') as front_end_server:
        ns.register(replica.name, uri, safe=True)
        print('Starting ' + str(replica.name) + '...')
        replica.set_id(front_end_server.register_replica(replica.name, replica))
        print("Registered %s" % str(replica.name))

    daemon.requestLoop()
