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
        self.players = players
        self.max_players = max_players
        self.joinable = max_players - len(players) > 0
        self.name = name
        self.field_size = field_size
        self.mine_prob = mine_prob

