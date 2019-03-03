If using a windows , or , operating system - start the program by running the batch file ('run.bat')

Wait until the replicas have been registered and this is displayed on the front end

To run the system, use main.bat, located in the base repository. By default, this launches 5 terminal windows - the Pyro name server, 1 frontend (FE), and 3 replicas (RM). The original terminal window serves as the client. By entering commands as the client, the propagation of requests and queries can be traced through the FE and the RMs.