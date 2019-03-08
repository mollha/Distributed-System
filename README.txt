If using a windows , or , operating system - start the program by running the batch file ('run.bat')

On a windows machine, start the program using the batch file (start.bat) by entering start.bat into the terminal
Wait until the replicas have been registered and this is displayed on the front end
Wait untill all 3 replicas are ready to receive requests

Talk about how to run if you can't run the bat script

I have included a delete method
I checked my code quality with pylint

If you are using a different operating system or if the batch files do not work, complete the following steps:
 1). Open a terminal and enter 'python -m Pyro4.naming' to start the Pyro nameserver
 2). In a NEW terminal, enter 'python -m front_end_server' to start the front end server
 3). In a NEW terminal, enter 'python -m replica'
 4). Repeat step 3 for each additional replica manager - each time using a new terminal

By default, this launches 6 terminal windows - the Pyro name server, 1 front-end server, 3 replica managers and a client.
By entering commands as the client, the propagation of requests and queries can be traced through the FE and the RMs.