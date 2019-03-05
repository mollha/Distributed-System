SET replicas = 3
echo %replicas %
start "Name Server" cmd /k python -m Pyro4.naming
timeout 1

FOR /L %%i IN (1,1,%replicas %) DO (
    start "Replica Manager %%i" cmd /k python -m Replica
)

timeout 10
start "Front End Server" cmd /k python -m FrontEndServer

timeout 10
start "Client" cmd /k python -m Client