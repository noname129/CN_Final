from network import async_socket
from network import smart_pipe
import json
from api.api_codes import RequestCodes
from util.utils import json_bytes_to_object, object_to_json_bytes
from api import api_datatypes

import collections

class ClientSideAPI():
    def __init__(self,addr,port):
        dt=async_socket.initiate_connection(addr, port)
        self._sp=smart_pipe.SmartPipe(dt)

        self._player_id=-1

    def login(self, username, cb_success, cb_fail):
        '''
        Log in to the server and get a player_id
        username:
            str
        cb_success(player_id):
            callback.
            player_id is saved to this object too, feel free to discard
        cb_fail(reason):
            callback fuynction
        '''
        def login_callback(resp):
            dat=json_bytes_to_object(resp)
            if dat["success"] == True:
                self._player_id=dat["player_id"]
                cb_success(dat["player_id"])
            else:
                cb_fail(dat["failure_reason"])

        self._sp.send_request(
            object_to_json_bytes({"username":username}),
            RequestCodes.JOIN,
            login_callback
        )

    def fetch_game_list(self, cb_data):
        '''
        Fetch the list of games

        cb_success(data):
            callback. data is a list of api_datatypes.GameRoomData
        '''
        def callback(resp):
            dat=json_bytes_to_object(resp)
            cb_data([api_datatypes.dict_to_namedtuple(i,api_datatypes.GameRoomData) for i in dat])

        self._sp.send_request(
            b'',
            RequestCodes.GET_GAME_LISTING,
            callback

        )
    def create_game(self, room_creation_parameters, cb_success, cb_fail):
        '''
        creat game

        room_creation_parameters:
            instance of api_datatypes.RoomCreationParameters

        cb_success(rid):
            callback function
            rid is the room ID of the created room.
        cb_fail(msg):
            callback function
            msg is the reason
        '''
        def callback(resp):
            dat=json_bytes_to_object(resp)
            if dat["success"]:
                cb_success(dat["created_room_id"])
            else:
                cb_fail(dat["failure_reason"])
        d=api_datatypes.namedtuple_to_dict(room_creation_parameters)
        j=object_to_json_bytes(d)
        self._sp.send_request(
            j,
            RequestCodes.CREATE_GAME,
            callback
        )


