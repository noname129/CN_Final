from network import smart_pipe
from api.api_codes import RequestCodes
import json
from api import api_datatypes
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





