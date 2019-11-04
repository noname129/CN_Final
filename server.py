port = int(input('Port:'))

server_sock = socket.socket(AF_INET, SOCK_STREAM)
server_sock.bind(('', port))

server_sock.listen()
