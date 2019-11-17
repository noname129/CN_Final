import socket
import threading
import pickle
from comms.common import *
import data.server_data

threads = []
threads_empty_idx = []
ingame_threads = []
ingame_threads_empty_idx = []

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
        client.sock.send(create_lobby_packet(LoginResponse(0, client.id)))

    elif protocol_number == int(Protocols.get_game_list_request):
        client.sock.send(create_lobby_packet(
            GetGameListResponse([t.game_instance.convert_to_tuple()
                                 for t in ingame_threads if t.game_instance.is_joinable()])))

    elif protocol_number == int(Protocols.create_room_request):
        if client.player_info.state == data.server_data.PlayerState.LOBBY:
            new_game = data.server_data.GameInstance(
                field_dimension=tuple(packet['fieldSize']),
                mine_probability=packet['mineProb'],
                max_players=packet['maxPlayers'],
                name=packet['name']
            )
            game_thread = IngameThread(new_game)
            ingame_threads[game_thread.id] = game_thread
            client.sock.send(create_lobby_packet(CreateRoomResponse(new_game.instance_id)))
        else:
            client.sock.send(create_lobby_packet(CreateRoomResponse(-1)))

    elif protocol_number == int(Protocols.join_room_request):
        if client.player_info.state == data.server_data.PlayerState.LOBBY:
            game = ingame_threads[data['roomId']].game_instance
            game.player_threads.append(client)
            client.sock.send(create_lobby_packet(JoinRoomResponse(game.convert_to_tuple())))
        else:
            client.sock.send(create_lobby_packet(JoinRoomResponse(None)))


class IngameThread(threading.Thread):
    def __init__(self, game_instance):
        threading.Thread.__init__(self)
        self.game_instance = game_instance
        self.id = IngameThread.new_index()
        self.game_instance.instance_id = self.id

    def run(self):
        pass

    @classmethod
    def new_index(cls):
        if len(ingame_threads_empty_idx) == 0:
            return len(ingame_threads)
        else:
            return ingame_threads_empty_idx.pop()


class ClientThread(threading.Thread):
    def __init__(self, sock, ip, port):
        threading.Thread.__init__(self)
        self.sock = sock
        self.ip = ip
        self.port = port
        self.process = process_lobby_packet
        self.id = ClientThread.new_index()
        self.player_info = data.server_data.Player('{}'.format(self.ip))

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
        threads_empty_idx.append(self.id)
        threads.remove(self)

    @classmethod
    def new_index(cls):
        if len(threads_empty_idx) == 0:
            return len(threads)
        else:
            return threads_empty_idx.pop()


def server_proc(port):
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind(('', port))

    server_sock.listen()

    while True:
        (client_sock, (ip, port)) = server_sock.accept()
        client_thread = ClientThread(client_sock, ip, port)
        client_thread.start()
        threads[client_thread.id] = client_thread

    for thread in threads:
        thread.join()
