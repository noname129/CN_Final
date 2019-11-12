from data import client_data
def login(ip, port, name, cb_success, cb_fail):
    '''
    Make a login request using the specified ip, port, and name.
    one of two callback functions will be called:
      cb_success(): login has succeded.
      cb_fail(msg): login has failed. A human-readable reasoning is provided as msg.
    '''
    # TODO implement

    print("STUB: GameClient.login")
    cb_success()


def fetch_game_list(cb_success, cb_fail):
    '''
    Fetch the game list.
    One of two callback functions will be called:
      cb_success(games): list of GameListing is returned through the games argument.
      cb_fail(msg): Failure. reason in msg.
    '''
    print("STUB: GameClient.fetch_game_list")
    # TODO implement

    cb_success([
        client_data.GameInstance(),
        client_data.GameInstance()
    ])

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



