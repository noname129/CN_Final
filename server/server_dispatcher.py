from network import async_socket
from api import server_api
from server import server_logic

gamelogic=server_logic.ServerSideGameLogic()

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