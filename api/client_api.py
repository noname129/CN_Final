from network import async_socket
from network import smart_pipe
import json
from api.api_codes import RequestCodes
from util.utils import json_bytes_to_object, object_to_json_bytes, restore_int_keys
from api import api_datatypes
import common.mines
import tkinter

import collections

class ClientSideAPI():
    def __init__(self,addr,port, tkRoot:tkinter.Tk):
        dt=async_socket.initiate_connection(addr, port)

        self._sp=smart_pipe.SmartPipe(dt)
        self._sp.set_callback_runner(lambda func: tkRoot.after_idle(func))

        self._player_id=-1

        self._sp.set_handler(
            self._base_handler_ingame_newstateACK,
            RequestCodes.INGAME_NEWSTATE_AND_ACK
        )
        self._handler_ingame_newstateACK=None

        self._sp.set_handler(
            self._base_handler_ingame_room_param_changed,
            RequestCodes.INGAME_NOTIFY_ROOM_PARAM_CHANGED
        )
        self._handler_ingame_room_param_changed = None

    def kill_connection(self):
        self._sp.kill_pipe()

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

    def join_game(self, player_id, room_id, cb_success, cb_fail):
        '''
        Join a game.

        room_id: the room ID that the player wishes to join

        sb_success(pidx):
            callback function
            pidx is the player index
        cb_fail(msg):
            callback functrion
            msg is the reason
        '''
        def callback(resp):
            dat=json_bytes_to_object(resp)
            if dat["success"]:
                cb_success(dat["room_id"], dat["player_index"])
            else:
                cb_fail(dat["failure_reason"])

        j=object_to_json_bytes({
            "player_id":player_id,
            "room_id":room_id
        })
        self._sp.send_request(
            j,
            RequestCodes.JOIN_GAME,
            callback
        )

    def ingame_input(self, roomMFI):
        '''
        Send a input to the server.

        player_input: an instance of api_datatypes.PlayerMFI
        '''

        d=api_datatypes.namedtuple_to_dict(roomMFI)
        j=object_to_json_bytes(d)

        self._sp.send_request(
            j,
            RequestCodes.INGAME_INPUT,
            None
        )

    def set_handler_ingame_newstateACK(self, handler):
        '''
        set handler for the INGAME_NEWSTATE_AND_ACK event

        handler function signature:
            handler(rmfi, mfs)
                rmfi: the RoomMFI object of the input that caused this update.
                      May be None, if there's no such input.
                mfs: the new state
        '''
        self._handler_ingame_newstateACK=handler

    def _base_handler_ingame_newstateACK(self,data):
        nul_place=0
        for i in range(len(data)):
            if data[i]==0: # the single NUL
                nul_place=i
                break
        part1_json=data[:nul_place]
        part2_binary=data[(nul_place+1):]
        j=json_bytes_to_object(part1_json)
        rmfi=api_datatypes.dict_to_namedtuple(j,api_datatypes.RoomMFI)
        mfs=common.mines.MineFieldState.from_bytes(part2_binary)
        self._handler_ingame_newstateACK(rmfi, mfs)

    def set_handler_ingame_room_param_changed(self,handler):
        '''
        handler is given the room id. No returns nessasary.
        '''
        self._handler_ingame_room_param_changed=handler

    def _base_handler_ingame_room_param_changed(self,data):
        f=self._handler_ingame_room_param_changed
        rid=json_bytes_to_object(data)["room_id"]
        if f is not None:
            f(rid)

    def ingame_fetch_room_params(self, room_id, cb_result, cb_fail):
        '''
        Fetch room parameters.

        room_id: the room ID

        sb_result(igrp):
            callback function
            igrp is an instance of api_datatypes.InGameRoomParameters
        cb_fail(msg):
            callback functrion
            msg is the reason
        '''
        def callback(resp):
            dat = json_bytes_to_object(resp)
            if dat["success"]:
                igrp=api_datatypes.dict_to_namedtuple(
                    restore_int_keys(dat["igrp"]),api_datatypes.InGameRoomParameters)
                cb_result(igrp)
            else:
                cb_fail(dat["failure_reason"])

        j = object_to_json_bytes({
            "room_id": room_id
        })
        self._sp.send_request(
            j,
            RequestCodes.INGAME_FETCH_ROOM_PARAMS,
            callback
        )

    def ingame_explicit_newstate_request(self, player_id):
        '''
        Request a newstate update to the server. No callbacks.
        player_id must be provided.
        '''
        self._sp.send_request(
            object_to_json_bytes({
                "player_id":player_id
            }),
            RequestCodes.INGAME_EXPLICIT_NEWSTATE_REQUEST,
            None
        )






