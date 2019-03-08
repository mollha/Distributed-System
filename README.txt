From a terminal, navigate to the base repository then start the system using the batch file (start.bat) by entering start.bat

This will start 6 separate terminals in the following order:
- the Pyro name server
- 1 front-end server
- 3 replica managers
- 1 client

- To add more clients, open a new terminal and enter 'python -m client'

I have implemented the following functionality:
READ - read a user rating and movie information (such as id, title, genres, year of production and average rating)
SUBMIT - submit a new user rating
UPDATE - overwrite a user rating with a new rating
DELETE - remove a user rating

If start.bat does not not work, complete the following steps:
 1). Open a terminal and enter 'python -m Pyro4.naming' to start the Pyro name server
 2). In a NEW terminal, enter 'python -m front_end_server' to start the front end server
 3). In a NEW terminal, enter 'python -m replica' to start a replica manager
 4). Repeat step 3 for each additional replica manager - each time using a new terminal
 5). In a NEW terminal, enter 'python -m client' to start a client
 6). Repeat step 5 for each additional client - each time using a new terminal