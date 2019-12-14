from common import mines
from api import server_api
import enum
from api import api_datatypes
from common import mines

class PlayerState(enum.Enum):
    LOBBY=1
    ROOM=2
    GAME=3

class Player:
    def __init__(self, name, player_id, server_connection:server_api.ServerSideAPI):
        self.username=name
        self.player_id=player_id
        self.state=PlayerState.LOBBY
        self.connection=server_connection

class GameInstance:
    def __init__(self, room_id, name, dimensions, mine_prob, max_players):
        self._room_id=room_id
        self._name=name
        self._dimensions=dimensions
        self._mine_prob=mine_prob
        self._max_players=max_players
        self._player_count=0
        self._active=False
        self._started=False
        self._message='Waiting for players...'

        self._players=[]
        self._player_to_index=dict()

        self._mfs=mines.MineFieldGenerator.generate_symmetrical(dimensions[0],
                                                                dimensions[1],
                                                                mine_prob/100,
                                                                max_players)

        self._explode_listeners=[]

    def add_explode_listener(self, func):
        self._explode_listeners.append(func)
    def explode(self):
        for i in self._explode_listeners:
            i()

        # We don't want to explode twice
        # remove all listeners so they won't get called twice
        self._explode_listeners=[]


    def has_player(self, player):
        return player in self._players

    def active_players(self):
        return tuple([self._player_to_index[i] for i in self._players])

    def add_input(self, rmfi:api_datatypes.RoomMFI):
        mfi=api_datatypes.mfi_extract(rmfi)
        self._mfs=self._mfs.process_input(mfi)

        for player in self._players:
            player.connection.send_newstateACK(rmfi, self._mfs)

        self.check_end_condition()
    def check_end_condition(self):
        if self._mfs.check_all_opened(self.active_players()):
            # Everything is opened - game is over!


            scores=self._mfs.calculate_scores()

            highest_score=-100000000
            winner=-1
            for k in scores:
                if scores[k]>highest_score:
                    highest_score=scores[k]
                    winner=k

            self._active = False
            self._message="Player {} wins!".format(winner)
            self.room_param_change_broadcast()

        if len(self._players)<2:
            self._message="You win!"
            self._active=False
            self.room_param_change_broadcast()

    def remove_player(self,player:Player):
        self._players.remove(player)

        if self._started:
            self.check_end_condition()

        self.room_param_change_broadcast()

        if len(self.players)==0:
            self.explode()


    def add_player(self,player:Player):
        if self._player_count == self._max_players:
            raise server_api.InvalidRequestException("Room full!")

        self._player_count += 1

        self._players.append(player)
        self._player_to_index[player]=self._player_count

        if self._player_count == self._max_players:
            self._active=True
            self._started=True
            self._message=None

        self.room_param_change_broadcast()

    def broadcast_activation(self):
        self._active=True
        self.room_param_change_broadcast()
    def broadcast_deactivation(self):
        self._active=False
        self.room_param_change_broadcast()

    def broadcast_message(self,msg):
        self._message=msg
        self.room_param_change_broadcast()

    def room_param_change_broadcast(self):
        for p in self._players:
            p.connection.send_notification_room_param_changed(self._room_id)

    def player_to_index(self, player):
        return self._player_to_index[player]

    @property
    def room_id(self):
        return self._room_id
    @property
    def players(self):
        return self._players
    @property
    def mfs(self):
        return self._mfs

    def to_game_room_data(self):
        return api_datatypes.GameRoomData(
            name=self._name,
            parameters="{}x{}@{:.03f}%".format(self._dimensions[0],self._dimensions[1],self._mine_prob),
            room_id=self._room_id,
            current_players=self._player_count,
            max_players=self._max_players,
            joinable=not self._started
        )
    def to_ingame_room_data(self):
        index_mapping=dict()
        names_mapping=dict()
        for p in self._players:
            pidx=self._player_to_index[p]
            index_mapping[pidx]=p.player_id
            names_mapping[pidx]=p.username
        return api_datatypes.InGameRoomParameters(
            player_index_mapping=index_mapping,
            player_names_mapping=names_mapping,
            field_size_x=self._mfs.x,
            field_size_y=self._mfs.y,
            max_players=self._max_players,
            game_active=self._active,
            popup_message=self._message
        )

class ServerSideGameLogic():
    def __init__(self):
        self._user_list=dict()
        self._player_id_base=1000

        self._game_list=dict()
        self._game_id_base=2000

        self._connections=[]

    def kill_all_connections(self):
        for i in self._connections:
            i.kill_connection()
    def add_connection(self, srvcon:server_api.ServerSideAPI):
        '''
        New connection
        '''
        srvcon.set_handler_join(
            lambda data:self._handle_add_player(data, srvcon))
        srvcon.set_handler_game_listing(
            self._handle_game_listing
        )
        srvcon.set_handler_game_creation(
            self._handle_game_creation
        )
        srvcon.set_handler_game_join(
            self._handle_game_join
        )
        srvcon.set_handler_ingame_input(
            self.handle_ingame_input
        )
        srvcon.set_handler_fetch_room_params(
            self._handle_fetch_room_params
        )
        srvcon.set_handler_explicit_newstate_request(
            self._handle_explicit_newstate_request
        )


        self._connections.append(srvcon)
    
    def disconnect_player(self, player):
        #player.username="(DISCONNECTED)"

        gi=self.find_game_with_user(player)
        if gi is not None:
            gi.remove_player(player)

        del self._user_list[player.player_id]

    def find_game_with_user(self, player):
        for game in self._game_list:
            if player in self._game_list[game].players:
                return self._game_list[game]



    def _handle_add_player(self, username, source_connection):
        for player_id in self._user_list:
            if self._user_list[player_id].username == username:
                raise server_api.InvalidRequestException("Duplicate username! Please choose another name.")
        self._player_id_base+=1
        player_id=self._player_id_base
        player=Player(
                username,
                player_id,
                source_connection
            )
        self._user_list[player_id]=player

        source_connection.set_handler_disconnect(
            lambda: self.disconnect_player(player)
        )

        return self._player_id_base

    def _handle_game_listing(self):
        result=[]
        for room_id in self._game_list:
            result.append(self._game_list[room_id].to_game_room_data())
        return result

    def _handle_game_creation(self, rcp:api_datatypes.RoomCreationParameters):
        self._game_id_base+=1
        game_id=self._game_id_base
        gi=GameInstance(
                self._game_id_base,
                rcp.name,
                (rcp.field_size_x,rcp.field_size_y),
                rcp.mine_prob,
                rcp.max_players
            )

        self._game_list[game_id]=gi

        gi.add_explode_listener(lambda:self._game_list.pop(game_id))

        return self._game_id_base

    def _validate_room_id(self,room_id):
        if room_id not in self._game_list:
            raise server_api.InvalidRequestException("WHAT? Invalid room id")
    def _validate_player_id(self,player_id):
        if player_id not in self._user_list:
            raise server_api.InvalidRequestException("WHAT? Invalid user id")

    def _handle_game_join(self, player_id, room_id):
        self._validate_player_id(player_id)
        self._validate_room_id(room_id)
        player=self._user_list[player_id]
        room=self._game_list[room_id]
        room.add_player(player)
        return room_id, room.player_to_index(player)

    def handle_ingame_input(self, rmfi:api_datatypes.RoomMFI):
        room_id=rmfi.roomID
        self._validate_room_id(room_id)

        room=self._game_list[room_id]
        room.add_input(rmfi)

    def _handle_fetch_room_params(self, room_id):
        self._validate_room_id(room_id)
        room=self._game_list[room_id]
        return room.to_ingame_room_data()

    def _handle_explicit_newstate_request(self,player_id):
        self._validate_player_id(player_id)
        player=self._user_list[player_id]

        room=self.find_game_with_user(player)
        player.connection.send_newstateACK(
            api_datatypes.RoomMFI(0,0,0,0,0,room.room_id),
            room.mfs)






