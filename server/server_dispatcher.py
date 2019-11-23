from network import async_socket
from api import server_api
from server import server_logic
import time

gamelogic=server_logic.ServerSideGameLogic()

connections=[]
def incoming_connection_handler(dt):
    serverconnection= server_api.ServerSideAPI(dt)
    gamelogic.add_connection(serverconnection)
    #serverconnections.append(serverconnection)

def start_server(host='', port=19477):
    async_socket.start_server(
        incoming_connection_handler,
        host,
        port
    )
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("^C received - killing all connections")
        gamelogic.kill_all_connections()
        async_socket.end_server(host,port)