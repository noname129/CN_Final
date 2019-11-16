'''
Defines datatypes that will be used client-side.
Most types here will mirror the types in server_data.py
but will have a pickle-able, immutable form - suitable for transfer through the network.
'''


class GameInstance:
    '''
    Client's view of the server's GameInstance.
    Immutable.
    '''
    def __init__(self, instance_id, players, max_players, name, field_size, mine_prob):
        # TODO actually make this class useful
        self.instance_id = instance_id
        # a tuple of player names [0] is player with index 1, and [1] 2, and so on.
        self.players = players
        self.max_players = max_players
        self.joinable = max_players - len(players) > 0
        self.name = name
        self.field_size = field_size
        self.mine_prob = mine_prob

# TODO consider converting these simple classes to namedtuples
class GameRoomParameters:
    '''
    A client's request to the server to create a game room.
    '''
    def __init__(self, max_players, name, field_size, mine_prob):
        self.max_players=max_players
        self.name=name
        self.field_size=field_size
        self.mine_prob=mine_prob

    def __repr__(self):
        return F"GameRoomParameters({self.max_players},{self.name},{self.field_size},{self.mine_prob})"