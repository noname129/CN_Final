from util import utils
from common import mines
from api import api_datatypes
from api import client_api

class ClientState:
    def __init__(self):
        self._pid=None
    def set_player_id(self, player_id):
        self._pid=player_id
    @property
    def player_id(self):
        return self._pid


class ClientInGameLogic():
    '''
    Actually handles user input and dispatches server communication requests
    '''
    def __init__(self, client_api:client_api.ClientSideAPI, player_index, room_id):


        # Since calculating the stats is a rather lengthy process,
        # We cache the board state, only updating when nessasary.
        self._state_cache=None
        self._score_cache=None

        self._event_stack= mines.MineFieldEventStack()

        self._current_input_index=0

        self._player_index=player_index
        self._room_id=room_id
        self._capi=client_api

        self._field_update_callbacks=[]
        self._room_update_callbacks=[]

        client_api.set_handler_ingame_newstateACK(self.handler_newstateACK)
        client_api.set_handler_ingame_room_param_changed(self.handler_room_param_change)

    def handler_room_param_change(self,rid):
        if rid == self._room_id:
            self.fetch_room_params()
    def fetch_room_params(self):
        self._capi.ingame_fetch_room_params(self.room_id,
                                            lambda igrp: self._call_room_update_callbacks(igrp),
                                            lambda: None)
    def add_field_update_callback(self,cb):
        self._field_update_callbacks.append(cb)
    def _call_field_update_callbacks(self):

        for i in self._field_update_callbacks:
            i()
    def add_room_update_callbaks(self,cb):
        self._room_update_callbacks.append(cb)
    def _call_room_update_callbacks(self, igrp):
        for i in self._room_update_callbacks:
            i(igrp)

    @property
    def player_index(self):
        return self._player_index
    @property
    def room_id(self):
        return self._room_id
    def debug_change_pidx(self,n):
        self._player_index=n

    def _invalidate_cache(self):
        self._state_cache=None
        self._score_cache=None


    def _recalculate_state_cache(self):
        self._state_cache=self._event_stack.calaulate_current_state()

    def _recalculate_score_cache(self):
        if self._state_cache is None:
            self._recalculate_state_cache()
        self._score_cache=self._state_cache.calculate_scores()

    def user_input(self,coords,button):
        self._current_input_index+=1
        mfi=mines.MineFieldInput(x=coords[0],
                                 y=coords[1],
                                 button=button,
                                 player_index=self._player_index)
        input_index=self._event_stack.add_input(mfi)

        self._invalidate_cache()
        self._call_field_update_callbacks()

        rmfi=api_datatypes.mfi_wrap(mfi,input_index,self._room_id)
        #print("## Send input",rmfi)
        self._capi.ingame_input(rmfi)


    def handler_newstateACK(self, rmfi:api_datatypes.RoomMFI, mfs:mines.MineFieldState):
        if (rmfi.roomID != self._room_id):
            raise Exception("what???????")

        #print("## Ackd input", rmfi)

        if (rmfi.player_index==self._player_index):
            # this ACK was directed at me!
            self._event_stack.ack_until(rmfi.inputID)

        self._event_stack.set_base_state(mfs)
        self._invalidate_cache()
        self._call_field_update_callbacks()



    def get_state(self):
        if self._state_cache is None:
            self._recalculate_state_cache()
        return self._state_cache
    def get_score(self):
        if self._score_cache is None:
            self._recalculate_score_cache()
        return self._score_cache