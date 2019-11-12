'''
Defines datatypes that will be used in server-side logic.
For data that needs to be sent to the client, a matching class will be found in client_data.py
'''

import enum
from data import client_data


class Player:
    name="playerrr"
    address="0.0.0.0:0"

class GameState(enum.Enum):
    IN_PROGRESS=enum.auto()
    NOT_STARTED=enum.auto()
    WAIT_FOR_PLAYERS=enum.auto()
    FINISHED=enum.auto()

class GameInstance:
    players=[]
    field_dimension = (40, 20)
    mine_probability=0.05
    max_players = 4
    state=GameState.WAIT_FOR_PLAYERS
    instance_id=123

    def convert_to_client_version(self):
        gi= client_data.GameInstance()
        # TODO implement


