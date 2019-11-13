import struct
import enum

# constant fields
SET_USER_NAME_REQUEST = 1
GET_USER_LIST_REQUEST = 2
GET_USER_LIST_RESPONSE = 3


class Protocols(enum.IntEnum):
    set_user_name_request = enum.auto()
    send_user_list = enum.auto()
    create_room_request = enum.auto()
    create_room_response = enum.auto()
    join_room_request = enum.auto()
    join_room_response = enum.auto()
    update_guest_name = enum.auto()
    start_game_request = enum.auto()
    start_game = enum.auto()


def create_packet(packet):
    values = packet.values
    fmt = packet.fmt
    packer = struct.Struct(fmt)
    return packer.pack(*values)


# packet examples
class SetUserNameRequest:
    fmt = 'I 16s'

    def __init__(self, name):
        if type(name) is not str or len(name) > 16:
            raise ValueError
        self.values = (SET_USER_NAME_REQUEST, name.encode('UTF-8'))


class GetUserListRequest:
    fmt = 'I'

    def __init__(self):
        self.values = (GET_USER_LIST_REQUEST,)


class SendUserList:
    @classmethod
    def var_fmt(cls, user_count):
        return 'I I' + ' 16s' * user_count

    def __init__(self, names):
        user_count = len(names)
        self.values = (GET_USER_LIST_RESPONSE, user_count) + names
        self.fmt = 'I I' + ' 16s' * user_count


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