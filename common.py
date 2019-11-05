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
    fmt = 'I 16s'

    def __init__(self, name):
        if type(name) is not str or len(name) > 16:
            raise ValueError
        self.values = (SET_USER_NAME_REQUEST, name.encode('UTF-8'))


class GetUserListRequest:
    fmt = 'I'

    def __init__(self):
        self.values = (GET_USER_LIST_REQUEST,)


class GetUserListResponse:
    @classmethod
    def var_fmt(cls, user_count):
        return 'I I' + ' 16s' * user_count

    def __init__(self, names):
        user_count = len(names)
        self.values = (GET_USER_LIST_RESPONSE, user_count) + names
        self.fmt = 'I I' + ' 16s' * user_count
