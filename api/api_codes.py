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
            "player_id":int,
            "room_id": int
        }
    response: (JSON)
        {
            "success": bool,
            "failure_reason": str,  << only if success=False
            "room_id":int,  << only if success=True
            "player_index":int  << only if success=True
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
            "player_index": int
            "input_id": int,
            "room_id":int
        } // api_datatypes.RoomMFI
    response: (NONE)
    '''

    INGAME_EXPLICIT_NEWSTATE_REQUEST=111
    '''
    INGAME_EXPLICIT_NEWSTATE_REQUEST
    Client -> Server
    request: (JSON)
        {
            "player_id":int
        }
    response:(NONE)
    // This is a special request, telling the server to send a NewState frame
    // even if there's no change.
    '''

    #INGAME_NEWSTATE = 110
    '''
    INGAME_NEWSTATE
    Server -> Client
    request: (BINARY)
        // common.mines.MineFieldState .to_bytes() .from_bytes()
    response: (NONE)
    '''

    INGAME_NEWSTATE_AND_ACK=113
    '''
    INGAME_NEWSTATE
    Server -> Client
    request: (COMPLEX)
        [0...n) (JSON)
            {
                "x": int,
                "y": int,
                "button": int,
                "player_index": int
                "input_id": int,
                "room_id":int
            } // api_datatypes.RoomMFI
        [n] NUL byte (\0)
        [n+1... (BINARY)
            // common.mines.MineFieldState .to_bytes() .from_bytes()
    response: (NONE)
    '''

    INGAME_NOTIFY_ROOM_PARAM_CHANGED=130
    '''
    INGAME_NOTIFY_ROOM_PARAM_CHANGED
    Server -> Client
    request: (JSON)
        {
            "room_id":int
        }
    response:(NONE)
    // This is a special request, notifying that the room parameter has changed.
    // Ideally the client should make a INGAME_FETCH_ROOM_PARAMS request
    // to get the newly updated data.
    '''

    INGAME_FETCH_ROOM_PARAMS=120
    '''
    INGAME_FETCH_ROOM_PARAMS
    Client -> Server
    request: (JSON)
        {
            "room_id":int
        }
    response: (JSON)
        {
            "success":bool,
            "igrp":
                {
                    "player_index_mapping": dict( player_index:int -> player_id:int ),
                    "player_names_mapping": dict( player_index:int -> player_name:str ),
                    "field_size_x": int,
                    "field_size_y": int,
                    "max_players": int(2 or 4),
                    "game_active": bool,
                    "popup_message": str
                }, <- only when success=true
            "failure_reason":str <- only when success=false
            
        }
    '''




    KEEPALIVE=200
    '''
    KEEPALIVE
    Server <-> Client
    request: (EMPTY)
    response: (EMPTY)    
    '''


