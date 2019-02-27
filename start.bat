start "Name Server" cmd /k python -m Pyro4.naming
start "Front End Server" cmd /k python -m front_end_server.py
sleep 10
FOR /L %%i IN (1,1,3) DO (
    start "Replica Manager %%i" cmd /k python -m Replica.py
)