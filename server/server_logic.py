from common import mines
from api import server_api
import enum
from api import api_datatypes

class PlayerState(enum.Enum):
    LOBBY=enum.auto()
    ROOM=enum.auto()
    GAME=enum.auto()

class Player:
    def __init__(self, name, player_id, server_connection:server_api.ServerSideAPI):
        self.username=name
        self.player_id=player_id
        self.state=PlayerState.LOBBY
        self.connection=server_connection

class GameInstance:
    def __init__(self, game_id, name, dimensions, mine_prob, max_players):
        self._game_id=game_id
        self._name=name
        self._dimensions=dimensions
        self._mine_prob=mine_prob
        self._max_players=max_players

        self._players=[]

    def add_player(self,player:Player):
        pass
    @property
    def game_id(self):
        return self._game_id

    def to_game_room_data(self):
        return api_datatypes.GameRoomData(
            self._name,
            "{}x{}@{:.03f}%".format(self._dimensions[0],self._dimensions[1],self._mine_prob),
            self._game_id,
            len(self._players),
            self._max_players,
            self._max_players==len(self._players)
        )

class ServerSideGameLogic():
    def __init__(self):
        self._user_list=[]
        self._player_id_base=1000

        self._game_list=[]
        self._game_id_base=2000



    def add_connection(self, srvcon:server_api.ServerSideAPI):
        '''
        New connection
        '''
        srvcon.set_handler_join(
            lambda data:self._handle_add_player(data, server_api))
        srvcon.set_handler_game_listing(
            self._handle_game_listing
        )
        srvcon.set_handler_game_creation(
            self._handle_game_creation
        )


    def _handle_add_player(self, username, source_connection):
        for players in self._user_list:
            if players.username == username:
                raise server_api.InvalidRequestException("Duplicate username! Please choose another name.")
        self._player_id_base+=1
        self._user_list.append(
            Player(
                username,
                self._player_id_base,
                source_connection
            )
        )
        return self._player_id_base

    def _handle_game_listing(self):
        result=[]
        for game_instance in self._game_list:
            result.append(game_instance.to_game_room_data())
        return result

    def _handle_game_creation(self, rcp:api_datatypes.RoomCreationParameters):
        self._game_id_base+=1
        self._game_list.append(
            GameInstance(
                self._game_id_base,
                rcp.name,
                (rcp.field_size_x,rcp.field_size_y),
                rcp.mine_prob,
                rcp.max_players
            )
        )
        return self._game_id_base



