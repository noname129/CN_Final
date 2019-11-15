import socket
import threading
from comms.common import *

threads = []
ingame_threads = []

def process_ingame_packet(client, data):
    protocol_number = int.from_bytes(data[:4], 'little')
    print('Receive packet type', protocol_number, 'from {}:{}'.format(client.ip, client.port))

    # if protocol_number == SET_USER_NAME_REQUEST:
    #     _, name = struct.unpack(SetUserNameRequest.fmt, data)
    #     client.user_name = name.decode('utf-8')
    # elif protocol_number == int(Protocols.send_user_list):
    #     names = tuple([client.user_name.encode('utf-8') for client in threads])
    #     client.sock.send(create_packet(SendUserList(names)))


def process_lobby_packet(client, data):
    data = json.loads(data.decode('utf-8'))
    print(data)
    protocol_number = data['protocol']
    print('Receive packet type', protocol_number, 'from {}:{}'.format(client.ip, client.port))

    if protocol_number == int(Protocols.login_request):
        client.user_name = data['userName']
        client.sock.send(create_lobby_packet(LoginResponse(0)))

    elif protocol_number == int(Protocols.get_game_list_request):
        client.sock.send(create_lobby_packet(
            GetGameListResponse([t.game_instance.convert_to_client_version() for t in ingame_threads])))


class IngameThread(threading.Thread):
    next_id = 1

    def __init__(self, game_instance):
        threading.Thread.__init__(self)
        self.game_instance = game_instance
        self.clients = []
        self.id = IngameThread.next_id

    def run(self):
        pass

class ClientThread(threading.Thread):
    next_id = 1

    def __init__(self, sock, ip, port):
        threading.Thread.__init__(self)
        self.sock = sock
        self.ip = ip
        self.port = port
        self.process = process_lobby_packet
        self.id = ClientThread.next_id
        self.user_name = '{}'.format(self.ip)

        ClientThread.next_id += 1

        print('Connection opened from {}:{}'.format(self.ip, self.port))

    def run(self):
        try:
            while True:
                data = self.sock.recv(2048)
                if len(data) == 0:
                    break
                self.process(self, data)
        except ConnectionResetError as err:
            print('Error occurred: ', err)
            pass

        print('Connection closed: {}:{}'.format(self.ip, self.port))
        threads.remove(self)


def server_proc(port):
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
