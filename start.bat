start "Name Server" cmd /k python -m Pyro4.naming
timeout 3
start "Front End Server" cmd /k python -m FrontEndServer
timeout 6
FOR /L %%i IN (1,1,3) DO (
    start "Replica Manager %%i" cmd /k python -m Replica
)
timeout 8
start "Client" cmd /k python -m Client