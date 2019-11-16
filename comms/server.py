import socket
import threading
import pickle
from comms.common import *
import data.server_data

threads = []
ingame_threads = []

def process_ingame_packet(client, packet):
    protocol_number = int.from_bytes(packet[:4], 'little')
    print('Receive packet type', protocol_number, 'from {}:{}'.format(client.ip, client.port))

    # if protocol_number == SET_USER_NAME_REQUEST:
    #     _, name = struct.unpack(SetUserNameRequest.fmt, data)
    #     client.user_name = name.decode('utf-8')
    # elif protocol_number == int(Protocols.send_user_list):
    #     names = tuple([client.user_name.encode('utf-8') for client in threads])
    #     client.sock.send(create_packet(SendUserList(names)))


def process_lobby_packet(client, packet):
    packet = json.loads(packet.decode('utf-8'))
    print(packet)
    protocol_number = packet['protocol']
    print('Receive packet type', Protocols(protocol_number), 'from {}:{}'.format(client.ip, client.port))

    if protocol_number == int(Protocols.login_request):
        client.player_info.name = packet['userName']
        client.sock.send(create_lobby_packet(LoginResponse(0)))

    elif protocol_number == int(Protocols.get_game_list_request):
        client.sock.send(create_lobby_packet(
            GetGameListResponse([t.game_instance.convert_to_tuple()
                                 for t in ingame_threads if t.game_instance.is_joinable()])))

    elif protocol_number == int(Protocols.create_room_request):
        if client.player_info.state == data.server_data.PlayerState.LOBBY:
            new_game = data.server_data.GameInstance(
                instance_id=IngameThread.next_id,
                field_dimension=tuple(packet['fieldSize']),
                mine_probability=packet['mineProb'],
                max_players=packet['maxPlayers'],
                name=packet['name']
            )
            new_game.player_threads.append(client)
            game_thread = IngameThread(new_game)
            ingame_threads.append(game_thread)
            client.sock.send(create_lobby_packet(CreateRoomResponse(new_game.instance_id)))
        else:
            client.sock.send(create_lobby_packet(CreateRoomResponse(-1)))

class IngameThread(threading.Thread):
    next_id = 1

    def __init__(self, game_instance):
        threading.Thread.__init__(self)
        self.game_instance = game_instance
        self.clients = []
        self.id = IngameThread.next_id

        IngameThread.next_id += 1

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
        self.player_info = data.server_data.Player('{}'.format(self.ip))

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

            # TODO remove player from IngameThread if belongs to one
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
