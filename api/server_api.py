from network import smart_pipe
from api.api_codes import RequestCodes
import json
from api import api_datatypes
import common.mines
from util.utils import json_bytes_to_object, object_to_json_bytes

class InvalidRequestException(Exception):
    pass

class ServerSideAPI:
    def __init__(self, dt):
        dt=dt
        self._sp=smart_pipe.SmartPipe(dt)
        self._sp.set_handler(
            self._raw_handle_join,
            RequestCodes.JOIN
        )
        self._handler_join=None

        self._handler_game_listing=None
        self._sp.set_handler(
            self._raw_handle_game_lsting,
            RequestCodes.GET_GAME_LISTING
        )

        self._handler_game_creation=None
        self._sp.set_handler(
            self._raw_handle_game_creation,
            RequestCodes.CREATE_GAME
        )

        self._handler_game_join = None
        self._sp.set_handler(
            self._raw_handle_game_join,
            RequestCodes.JOIN_GAME
        )

        self._handler_ingame_input = None
        self._sp.set_handler(
            self._raw_handle_ingame_input,
            RequestCodes.INGAME_INPUT
        )

        self._handler_fetch_room_params = None
        self._sp.set_handler(
            self._raw_handle_fetch_room_params,
            RequestCodes.INGAME_FETCH_ROOM_PARAMS
        )

        self._handler_explicit_newstate_request = None
        self._sp.set_handler(
            self._raw_handle_explicit_newstate_request,
            RequestCodes.INGAME_EXPLICIT_NEWSTATE_REQUEST
        )

    def kill_connection(self):
        print("Killing ServerSideAPI")
        self._sp.kill_pipe()

    def add_data_receive_callback(self, cb):
        self._sp.add_data_receive_callback(cb)

    def remove_data_receive_callback(self, cb):
        self._sp.remove_data_receive_callback(cb)

    def add_connection_error_callback(self, cb):
        self._sp.remove_data_receive_callback(cb)

    def add_connection_close_callback(self, cb):
        self._sp.add_connection_close_callback(cb)

    def set_handler_join(self, handler):
        '''
        Set the handler for newly joining players
        handler function signature:
        arguments:
            username (str)
        returns:
            player_id (int)
        may raise:
            InvalidRequestException
        '''
        self._handler_join=handler

    def _raw_handle_join(self, data):
        unpacked=json_bytes_to_object(data)

        try:
            player_id=self._handler_join(unpacked["username"])
            return object_to_json_bytes({
                "success":True,
                "player_id":player_id
            })
        except InvalidRequestException as e:
            return object_to_json_bytes({
                "success": False,
                "failure_reason": str(e)
            })

    def set_handler_game_listing(self,handler):
        '''
        arguments: None
        returns: list of GameRoomData (defined in api_codes.py)
        '''
        self._handler_game_listing=handler

    def _raw_handle_game_lsting(self, data):

        # no data
        return object_to_json_bytes(
            [api_datatypes.namedtuple_to_dict(i) for i in self._handler_game_listing()]
        )

    def set_handler_game_creation(self,handler):
        '''
        Arguments: a RoomCreationParameters object
        returns: the created room id
        '''
        self._handler_game_creation=handler

    def _raw_handle_game_creation(self,data):
        unpacked=json_bytes_to_object(data)
        rcp=api_datatypes.dict_to_namedtuple(unpacked,api_datatypes.RoomCreationParameters)

        try:
            room_id = self._handler_game_creation(rcp)
            return object_to_json_bytes({
                "success": True,
                "created_room_id": room_id
            })
        except InvalidRequestException as e:
            return object_to_json_bytes({
                "success": False,
                "failure_reason": str(e)
            })

    def set_handler_game_join(self, handler):
        '''
        Arguments: player id, room id
        returns: room id, player index
        may raise: InvalidRequestException
        '''
        self._handler_game_join=handler

    def _raw_handle_game_join(self,data):
        unpacked=json_bytes_to_object(data)

        try:
            rid, pidx = self._handler_game_join(unpacked["player_id"],unpacked["room_id"])
            return object_to_json_bytes({
                "success": True,
                "room_id": rid,
                "player_index": pidx
            })
        except InvalidRequestException as e:
            return object_to_json_bytes({
                "success": False,
                "failure_reason": str(e)
            })

    def set_handler_ingame_input(self, handler):
        '''
        Argument: api_datatypes.RoomMFI
        returns: none
        '''
        self._handler_ingame_input=handler

    def _raw_handle_ingame_input(self, data):
        d=json_bytes_to_object(data)
        rmfi=api_datatypes.dict_to_namedtuple(d,api_datatypes.RoomMFI)

        self._handler_ingame_input(rmfi)


    def send_newstateACK(self, rmfi:api_datatypes.RoomMFI, mfs:common.mines.MineFieldState):
        res=bytes()
        res += object_to_json_bytes(api_datatypes.namedtuple_to_dict(rmfi))
        res+= bytes((0,))
        res += common.mines.MineFieldState.to_bytes(mfs)
        self._sp.send_request(
            res,
            RequestCodes.INGAME_NEWSTATE_AND_ACK,
            None # no callback
        )
    def send_notification_room_param_changed(self,room_id):
        self._sp.send_request(
            object_to_json_bytes({"room_id":room_id}),
            RequestCodes.INGAME_NOTIFY_ROOM_PARAM_CHANGED,
            None
        )

    def set_handler_fetch_room_params(self,handler):
        '''
        Argument: room id
        returns: InGameRoomParams
        may raise InvalidRequestException
        '''
        self._handler_fetch_room_params=handler

    def _raw_handle_fetch_room_params(self, data):
        d=json_bytes_to_object(data)
        room_id=d["room_id"]
        try:
            igrp=self._handler_fetch_room_params(room_id)
            d=api_datatypes.namedtuple_to_dict(igrp)
            j=object_to_json_bytes({
                "success":True,
                "igrp":d
            })
            return j
        except InvalidRequestException as e:
            return object_to_json_bytes({
                "success": False,
                "failure_reason": str(e)
            })

    def set_handler_explicit_newstate_request(self,handler):
        '''
        Argument: player_id
        returns: none
        '''
        self._handler_explicit_newstate_request=handler

    def _raw_handle_explicit_newstate_request(self,data):
        player_id=json_bytes_to_object(data)["player_id"]
        self._handler_explicit_newstate_request(player_id)



