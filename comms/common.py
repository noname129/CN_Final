import struct
import enum
import json

# constant fields
SET_USER_NAME_REQUEST = 1
GET_USER_LIST_REQUEST = 2
GET_USER_LIST_RESPONSE = 3


class Protocols(enum.IntEnum):
    login_request = enum.auto()
    login_response = enum.auto()
    get_game_list_request = enum.auto()
    get_game_list_response = enum.auto()
    create_room_request = enum.auto()
    create_room_response = enum.auto()
    join_room_request = enum.auto()
    join_room_response = enum.auto()
    update_guest_name = enum.auto()
    start_game_request = enum.auto()
    start_game = enum.auto()


def create_ingame_packet(packet):
    values = packet.values
    fmt = packet.fmt
    packer = struct.Struct(fmt)
    return packer.pack(*values)


def create_lobby_packet(packet):
    return json.dumps(packet.values).encode('utf-8')


# ========================= lobby packets =========================
class LoginRequest:
    def __init__(self, user_name):
        self.values = {
            'protocol': int(Protocols.login_request),
            'userName': user_name
        }


class LoginResponse:
    def __init__(self, code):
        self.values = {
            'protocol': int(Protocols.login_response),
            'code': code
        }


class GetGameListRequest:
    def __init__(self):
        self.values = {
            'protocol': int(Protocols.get_game_list_request)
        }


class GetGameListResponse:
    def __init__(self, waiting_game_list):
        self.values = {
            'protocol': int(Protocols.get_game_list_response),
            'gameList': waiting_game_list
        }

# ========================= belows are not refactored yet =========================

class CreateRoomRequest:
    fmt = 'I I I'

    def __init__(self, board_width, board_height):
        self.values = (int(Protocols.create_room_request), board_width, board_height)


class CreateRoomRequest:
    fmt = 'I I I I'

    def __init__(self, code, board_width, board_height):
        self.values = (int(Protocols.create_room_request), code, board_width, board_height)


class JoinRoomRequest:
    fmt = 'I I'

    def __init__(self, room_number):
        self.values = (int(Protocols.join_room_request), room_number)


class JoinRoomResponse:
    fmt = 'I I 16s I I'

    def __init__(self, room_number, opponent_name, board_width, board_height):
        self.values = (int(Protocols.join_room_response), room_number, opponent_name, board_width, board_height)


class UpdateGuestName:
    fmt = 'I 16s'

    def __init__(self, opponent_name):
        self.values = (int(Protocols.update_guest_name), opponent_name)


class StartGame:
    fmt = 'I'

    def __init__(self):
        self.values = (int(Protocols.start_game),)