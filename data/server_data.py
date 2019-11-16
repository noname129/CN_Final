'''
Defines datatypes that will be used in server-side logic.
For data that needs to be sent to the client, a matching class will be found in client_data.py
'''

import enum
from data import client_data


class Player:
    def __init__(self, name):
        self.name = name

class GameState(enum.Enum):
    IN_PROGRESS=enum.auto()
    NOT_STARTED=enum.auto()
    WAIT_FOR_PLAYERS=enum.auto()
    FINISHED=enum.auto()

class GameInstance:
    def __init__(self, instance_id, field_dimension=(40, 20), mine_probability=0.05, max_players=4):
        self.player_threads = []
        self.instance_id = instance_id
        self.state = GameState.WAIT_FOR_PLAYERS
        self.field_dimension = field_dimension
        self.mine_probability = mine_probability
        self.max_players = max_players

    def convert_to_client_version(self):
        gi = client_data.GameInstance(
            instance_id=self.instance_id,
            players=tuple([player.player_info.name for player in self.player_threads]),
            max_players=self.max_players,
            name=self.player_threads[0].player_info.name if len(self.player_threads) > 0 else "Ghost Room",
            field_size=self.field_dimension,
            mine_prob=self.mine_probability
        )
        return gi

    def is_joinable(self):
        return self.state == GameState.WAIT_FOR_PLAYERS and self.max_players - len(self.player_threads) > 0

