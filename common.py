import struct

# constant fields
SET_USER_NAME_REQUEST = 1
GET_USER_LIST_REQUEST = 2
GET_USER_LIST_RESPONSE = 3


def create_packet(packet):
    values = packet.values
    fmt = packet.fmt
    packer = struct.Struct(fmt)
    return packer.pack(*values)


# packet examples
class SetUserNameRequest:
    def __init__(self, name):
        if type(name) != 'str' or len(name) > 16:
            raise ValueError
        self.values = (SET_USER_NAME_REQUEST, name)
        self.fmt = 'I 16s'


class GetUserListRequest:
    def __init__(self):
        self.values = (GET_USER_LIST_REQUEST,)
        self.fmt = 'I'


class GetUserListResponse:
    def __init__(self, user_count, names):
        self.values = (GET_USER_LIST_RESPONSE, user_count) + names
        self.fmt = 'I I' + ' 16s' * user_count
