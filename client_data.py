'''
Defines datatypes that will be used client-side.
Most types here will mirror the types in server_data.py
but will have a pickle-able, immutable form - suitable for transfer through the network.
'''

import callbacks


class GameInstance:
    '''
    Client's view of the server's GameInstance.
    Immutable.
    '''
    def __init__(self):
        # TODO actually make this class useful
        self.players=("asdf","qwer","zxcv")
        self.max_players=4
        self.joinable=True
        self.instance_id=123
        self.name="A game!"
        self.field_size=(40,20)
        self.mine_prob=0.05

