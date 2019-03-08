SET replicas = 3
echo %replicas %
start "Name Server" cmd /k python -m Pyro4.naming
timeout 1

start "Front End Server" cmd /k python -m front_end_server
timeout 6

FOR /L %%i IN (1,1,%replicas %) DO (
    timeout 1
    start "Replica Manager %%i" cmd /k python -m replica
)

timeout 12
start "Client" cmd /k python -m client