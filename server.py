import socket
import threading

threads = []


def process_packet(data):
    protocol_number = int.from_bytes(data[:4], 'little')
    print(protocol_number)


class ClientThread(threading.Thread):
    def __init__(self, sock, ip, port):
        threading.Thread.__init__(self)
        self.sock = sock
        self.ip = ip
        self.port = port
        self.process = process_packet

        print('Connection from {}:{}'.format(self.ip, self.port))

    def run(self):
        try:
            while True:
                data = self.sock.recv(2048)
                if len(data) == 0:
                    break
                process_packet(data)
        except ConnectionResetError as err:
            print('Error occurred: ', err)
            pass

        print('Connection closed: {}:{}'.format(self.ip, self.port))
        threads.remove(self)


if __name__ == '__main__' :
    port = int(input('Port:'))

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind(('', port))

    server_sock.listen()

    while True:
        (client_sock, (ip, port)) = server_sock.accept()
        client_thread = ClientThread(client_sock, ip, port)
        client_thread.start()
        threads.append(client_thread)

    for thread in threads:
        thread.join()
