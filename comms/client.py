import tkinter
import socket
import threading
import queue
import json
import enum
from comms.common import *


class ClientState(enum.Enum):
    lobby = enum.auto()
    ingame = enum.auto()


_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
_sock.settimeout(10.0)
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

def process_lobby_packet(data):
    data = json.loads(data.decode('utf-8'))
    protocol_number = data['protocol']
    print('Receive packet type', protocol_number)
    callback_number = -1  #0 : succeed, 1 : fail

    if protocol_number == int(Protocols.login_response):
        if data['code'] == 0:
            callback_number = 0

    if callback_number >= 0:
        try:
            cb_lists[protocol_number].get()[callback_number]()
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
