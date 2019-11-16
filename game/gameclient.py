from data import client_data
import comms.client
from comms.common import *
def login(ip, port, name, cb_success, cb_fail):
    '''
    Make a login request using the specified ip, port, and name.
    one of two callback functions will be called:
      cb_success(): login has succeded.
      cb_fail(msg): login has failed. A human-readable reasoning is provided as msg.
    '''
    # TODO implement

    if name == '':
        cb_fail('')

    connection_attempt = comms.client.connect(ip, port, name)
    if connection_attempt != 0:
        cb_fail(connection_attempt)
    else:
        comms.client.send_packet(create_lobby_packet(LoginRequest(user_name=name)))
        comms.client.cb_lists[Protocols.login_response].put_nowait((cb_success, cb_fail))

    print("STUB: GameClient.login")


def fetch_game_list(cb_success, cb_fail):
    '''
    Fetch the game list.
    One of two callback functions will be called:
      cb_success(games): list of GameListing is returned through the games argument.
      cb_fail(msg): Failure. reason in msg.
    '''

    comms.client.send_packet(create_lobby_packet(GetGameListRequest()))
    comms.client.cb_lists[Protocols.get_game_list_response].put_nowait((cb_success, cb_fail))

    print("STUB: GameClient.fetch_game_list")

def create_game(game_room_params,cb_success,cb_fail):
    '''
    Create a game, using the parameters supplied in game_room_params (instance of GameRoomParameters)
    One of two callback functions will be called:
      cb_success(instance_id): The instance ID of the created room.
                               The client then may try to join the room immediately.
      cb_fail(msg): Failure. reason in msg.
    '''

    print("STUB: GameClient.create_game")

    comms.client.send_packet(create_lobby_packet(CreateRoomRequest(
        max_players=game_room_params.max_players,
        name=game_room_params.name,
        field_size=game_room_params.field_size,
        mine_prob=game_room_params.mine_prob
    )))
    comms.client.cb_lists[Protocols.create_room_response].put_nowait((cb_success, cb_fail))

def join_game(gid,cb_success, cb_fail):
    '''
    Request to join a game, specified by gid.
    One of two callback functions will be called:
      cb_success(gi): the player that has sent this request has successfully joined the game.
                      a GameInstance of the game is returned.
      cb_fail(msg): Failure. reason in msg.
    '''
    # TODO implement
    print("STUB: GameClient.join_game")

    cb_success(gid)



