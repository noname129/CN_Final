import collections

def namedtuple_to_dict(nt):
    return nt._asdict()

def dict_to_namedtuple(d,nt_class):
    return nt_class(*[ d[field] for field in nt_class._fields])

GameRoomData = collections.namedtuple("GameRoomData",
                                  ("name",
                                   "parameters",
                                   "room_id",
                                   "current_players",
                                   "max_players",
                                   "joinable"))

RoomCreationParameters = collections.namedtuple("RoomCreationParameters",
                                                ("name",
                                                "field_size_x",
                                                "field_size_y",
                                                "mine_prob",
                                                "max_players"))