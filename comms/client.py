import tkinter
import socket
import threading
import queue
import json
import data.client_data
import enum
from comms.common import *


class ClientState(enum.Enum):
    lobby = enum.auto()
    ingame = enum.auto()


_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
_sock.settimeout(10.0)
client_id = None
_state = None

cb_lists = [queue.Queue() for i in range(len(Protocols))]


def process_ingame_packet(data):
    protocol_number = int.from_bytes(data[:4], 'little');
    print('Receive packet type', protocol_number)

    if protocol_number == int(Protocols.login_response):
        res = struct.unpack(LoginResponse.fmt, data)
        # if res[1] == some succeed code


    # if protocol_number == GET_USER_LIST_RESPONSE:
    #     user_count = int.from_bytes(data[4:8], 'little')
    #     res = struct.unpack(GetUserListResponse.var_fmt(user_count), data)
    #     for i in range(2, user_count + 2):
    #         print(res[i].decode('utf-8'))

def process_lobby_packet(packet):
    packet = json.loads(packet.decode('utf-8'))
    protocol_number = packet['protocol']
    print('Receive packet type', protocol_number)
    callback_number = -1  #0 : succeed, 1 : fail
    callback_args = []

    if protocol_number == int(Protocols.login_response):
        if packet['code'] == 0:
            global client_id
            callback_number = 0
            client_id = packet['userId']
    elif protocol_number == int(Protocols.get_game_list_response):
        if len(packet['gameList']) > 0:
            callback_number = 0
            game_list = tuple([data.client_data.GameInstance(*game) for game in packet['gameList']])
            callback_args.append(game_list)
        else:
            callback_number = 1
            callback_args.append('There are no games available.')
    elif protocol_number == int(Protocols.create_room_response):
        if packet['roomId'] >= 0:
            callback_number = 0
            callback_args.append(packet['roomId'])
        else:
            callback_number = 1
            callback_args.append('You are already inside a room.')
    elif protocol_number == int(Protocols.join_room_response):
        if packet['gameInfo'] is not None:
            callback_number = 0
            gi = data.client_data.GameInstance(*packet['gameInfo'])
            callback_args.append(gi)
            callback_args.append(client_id)
        else:
            callback_number = 1
            callback_args.append('Invalid attempt.')


    if callback_number >= 0:
        try:
            print(tuple(callback_args))
            cb_lists[protocol_number].get()[callback_number](*(tuple(callback_args)))
        except queue.Empty:
            pass


def send_packet(data):
    _sock.send(data)


def receive_packet():
    while True:
        data = _sock.recv(2048)
        if _state == ClientState.lobby:
            process_lobby_packet(data)


def connect(ip, port, name):
    global _state

    try:
        _sock.connect((ip, port))
    except socket.error as err:
        print('socket.error :', err)
        return err

    _sock.settimeout(None)
    _state = ClientState.lobby

    receiver = threading.Thread(target=receive_packet)
    receiver.start()
    return 0


def close_event():
    _sock.close()
