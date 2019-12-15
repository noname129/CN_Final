
import sys

DEFAULT_PORT = 19477

if len(sys.argv)>1 and sys.argv[1]=="-server":

    port = DEFAULT_PORT
    if len(sys.argv) > 2 and sys.argv[2].startswith("--port="):
        port = int(sys.argv[2][7:])

    import server.server_dispatcher
    server.server_dispatcher.start_server(port=port,host='')

else:
    import client.client_ui
    client.client_ui.start()
