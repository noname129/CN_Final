class RequestCodes():
    '''
    A enum of request codes.
    Also serves as an API reference for all the requests.
    '''

    JOIN = 10
    '''
    JOIN
    Client -> Server
    request: (JSON)
        {
            "username": str
        }
    response: (JSON)
        {
            "success": bool,
            "player_id": int,  << only if success=True
            "failure_reason": str << only if success=False
        }
    '''


    GET_GAME_LISTING = 20
    '''
    GET_GAME_LISTING
    Client -> Server
    request: (EMPTY)
    response: (JSON)
        [
            {
                "name": str,
                "parameters": str,
                "room_id": int,
                "current_players": int,
                "max_players": int,
                "joinable": bool
            } // use api_datatypes.GameRoomData
            , ...
        ]
        
    '''


    CREATE_GAME=21
    '''
    CREATE_GAME
    Client -> Server
    request: (JSON)
        {
            "name": str,
            "field_size_x": int,
            "field_size_y": int,
            "mine_prob": float,
            "max_players": int
        } // api_datatypes.RoomCreationParameters
    response: (JSON)
        {
            "success": bool,
            "failure_reason": str,  << only if success=False
            "created_room_id": int  << only if success=True
        }
    '''


    JOIN_GAME=31
    '''
    JOIN_GAME
    Client -> Server
    request: (JSON)
        {   
            "player_id",
            "room_id": int
        }
    response: (JSON)
        {
            "success": bool,
            "failure_reason": str,  << only if success=False
            "joined_room_id": int  << only if success=True
        }
    '''

    INGAME_INPUT=100
    '''
    INGAME_INPUT
    Client -> Server
    request: (JSON)
        {
            "x": int,
            "y": int,
            "button": int,
            "input_id": int,
            "player_id": int
        }
    '''

    INGAME_NEWSTATE = 110
    '''
    INGAME_NEWSTATE
    Server -> Client
    request: (BINARY)
        bytestream, 1 byte per cell
            bits 0~1: state
            bits 2  : is_mine
            bits 3~4: owner
        total x*y bytes
    response: (NONE)
    '''

    INGAME_ACK=111
    '''
    INGAME_ACK
    Server -> Client
    request: (JSON)
        {
            "player_id": int,
            "input_id": int
        }
    response: (NONE)    
    '''


    INGAME_NEW_ROOM_PARAM=112
    '''
    INGAME_NEW_ROOM_PARAM
    Server -> Client
    request: (JSON)
        {
            "player_index_mapping": dict( player_index:int -> player_id:int ),
            "player_names_mapping": dict( player_index:int -> player_name:str ),
            "field_size_x": int,
            "field_size_y": int
        }
    '''


    INGAME_NEW_BOARD=113



    KEEPALIVE=200
    '''
    KEEPALIVE
    Server <-> Client
    request: (EMPTY)
    response: (EMPTY)    
    '''


