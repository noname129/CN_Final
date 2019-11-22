import collections
import common.mines

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

InGameRoomParameters = collections.namedtuple("InGameRoomParameters",
                                              ("player_index_mapping",
                                               "player_names_mapping",
                                               "field_size_x",
                                               "field_size_y",
                                               "max_players"))

# common.mines.MineFieldInput + some metadata
RoomMFI = collections.namedtuple("RoomMFI",
                                 ("x","y","button","player_index","inputID","roomID"))
def mfi_wrap(mfi, input_id, room_id):
    # MineFieldInput -> RoomMFI
    return RoomMFI(
        x=mfi.x,
        y=mfi.y,
        button=mfi.button,
        player_index=mfi.player_index,
        inputID=input_id,
        roomID=room_id
    )
def mfi_extract(room_mfi):
    # RoomMFI -> MineFieldInput
    return dict_to_namedtuple(namedtuple_to_dict(room_mfi),common.mines.MineFieldInput)

