from util import utils
from common import mines


class ClientState:
    def __init__(self):
        pass
    def set_player_id(self, player_id):
        pass


class ClientInGameLogic(utils.CallbackEnabledClass):
    '''
    Actually handles user input and dispatches server communication requests
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args,**kwargs)

        # Since calculating the stats is a rather lengthy process,
        # We cache the board state, only updating when nessasary.
        self._state_cache=None
        self._score_cache=None

        self._event_stack= mines.MineFieldEventStack()

        self._current_input_index=0

    @property
    def player_index(self):
        return self._player_index
    def debug_change_pidx(self,n):
        self._player_index=n
    def _invalidate_cache(self):
        self._state_cache=None
        self._score_cache=None


    def _recalculate_state_cache(self):
        '''
        lazy recalculation
        '''
        self._state_cache=self._event_stack.calaulate_current_state()

    def _recalculate_score_cache(self):
        if self._state_cache is None:
            self._recalculate_state_cache()
        self._score_cache=self._state_cache.calculate_scores()

    def user_input(self,coords,button):
        self._current_input_index+=1
        self._event_stack.add_input(
            mines.MineFieldInput(x=coords[0],
                                 y=coords[1],
                                 button=button,
                                 player_index=self._player_index,
                                 input_index=self._current_input_index))

        self._invalidate_cache()
        self._call_update_callbacks()

    def receive_data_from_server(self, ack, newstate):
        if ack.player_index == self._player_index:
            self._event_stack.ack_until(ack.input_index)

        self._event_stack.set_base_state(newstate)
        self._invalidate_cache()
        self._call_update_callbacks()

    def server_sync(self,newstate):
        self._event_stack.set_base_state(newstate)
        self._invalidate_cache()
        self._call_update_callbacks()
    def get_state(self):
        if self._state_cache is None:
            self._recalculate_state_cache()
        return self._state_cache
    def get_score(self):
        if self._score_cache is None:
            self._recalculate_score_cache()
        return self._score_cache