
import sys
print(sys.argv)

DEFAULT_PORT = 19477

if len(sys.argv)>1 and sys.argv[1]=="-server":
    import comms.server

    port = DEFAULT_PORT
    if len(sys.argv) > 2 and sys.argv[2].startswith("--port="):
        port = int(sys.argv[2][7:])

    comms.server.server_proc(port)
else:
    import gui.client_ui

    gui.client_ui.start()
