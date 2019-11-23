'''
Adds various functionality on top of network.async_socket.AsyncSocket

Please refer to the docstring of SmartPipe for details.
'''

from network import async_socket
from util.utils import perline_prefix, extract_bit



class _IncompleteFrameException(Exception):
    pass

class _SmartPipeFrame:
    '''
    Binary data structure, used by SmartPipe

    SmartPipe frame structure
    [0] FLAGS
        bit 0: response_expected
        bit 1: is_response
    [1..5) LENGTH
        Length of the payload, EXCLUDING the header.
    [5..9) REQUEST_ID
        Request ID. One for each request.
    [9..11) RQTYPE
        Requst type.
    [11...? PAYLOAD (variable length)
    '''
    _pos_flags = slice(0, 1)
    _pos_flags_response_expected_bit = 0
    _pos_flags_is_response_bit = 1
    _pos_length = slice(1, 5)
    _pos_request_id = slice(5, 9)
    _pos_rqtype = slice(9, 11)
    _header_length = 11

    def __init__(self, *, response_expected, is_response, length, request_id, rqtype, payload):
        '''
        avoid calling this directly! Use the classmethod frame_create instead.
        frame_create makes sure the length parameter matches the payload length
        but this constructor does not check for that
        '''
        self._response_expected=response_expected
        self._is_response=is_response
        self._length=length
        self._request_id=request_id
        self._rqtype=rqtype
        self._payload=payload
    @property
    def response_expected(self):
        return self._response_expected
    @property
    def is_response(self):
        return self._is_response
    @property
    def length(self):
        return self._length
    @property
    def request_id(self):
        return self._request_id
    @property
    def request_type(self):
        return self._rqtype
    @property
    def payload(self):
        return self._payload
    def __str__(self):
        s=''
        s+= "{:<20s}: {}\n".format("response_expected",self.response_expected)
        s += "{:<20s}: {}\n".format("is_response", self.is_response)
        s += "{:<20s}: {}\n".format("length", self.length)
        s += "{:<20s}: {}\n".format("request_id", self.request_id)
        s += "{:<20s}: {}\n".format("request_type", self.request_type)

        pl=str(self.payload)
        if len(pl)>250:
            pl="(blob, {} bytes)".format(len(self.payload))
        s += "{:<20s}: {}".format("payload", pl)
        return s

    @classmethod
    def frame_create(cls, *, payload, response_expected, is_response, request_id, request_type):
        '''
        constructor
        '''
        length = len(payload)
        return _SmartPipeFrame(
            response_expected=response_expected,
            is_response=is_response,
            length=length,
            request_id=request_id,
            rqtype=request_type,
            payload=payload
        )

    @classmethod
    def frame_unpack(cls, buffer:bytes):
        '''
        bytes -> SmartPipeFrame
        '''
        if len(buffer) < cls._header_length:
            raise _IncompleteFrameException

        flags = buffer[cls._pos_flags][0]
        response_expected = extract_bit(flags, cls._pos_flags_response_expected_bit)
        is_response = extract_bit(flags, cls._pos_flags_is_response_bit)
        length = int.from_bytes(buffer[cls._pos_length],"big")
        request_id = int.from_bytes(buffer[cls._pos_request_id],"big")
        rqtype = int.from_bytes(buffer[cls._pos_rqtype],"big")

        if len(buffer) - cls._header_length < length:
            raise _IncompleteFrameException

        payload = buffer[cls._header_length:cls._header_length + length]

        spf= _SmartPipeFrame(
            response_expected=response_expected,
            is_response=is_response,
            length=length,
            request_id=request_id,
            rqtype=rqtype,
            payload=payload
        )

        return spf,(cls._header_length + length)

    @classmethod
    def frame_pack(cls, spf):
        '''
        SmartPipeFrame -> bytes
        '''
        result=bytes()

        flags=0
        if spf.response_expected:
            flags |= 1 << cls._pos_flags_response_expected_bit
        if spf.is_response:
            flags |= 1 << cls._pos_flags_is_response_bit

        result += bytes((flags,))
        result+= int(spf.length).to_bytes(cls._pos_length.stop-cls._pos_length.start,"big")
        result += int(spf.request_id).to_bytes(cls._pos_request_id.stop - cls._pos_request_id.start, "big")
        result += int(spf.request_type).to_bytes(cls._pos_rqtype.stop - cls._pos_rqtype.start, "big")
        result += spf.payload

        return result



class SmartPipe():
    '''
    A intelligent data exchange mechanism, runs on top of AsyncSocket.
    This adds several features over a dumb pipe:
     - Message Separation
        Each message sent over the socket will have a length field automatically attached.
        This allows the receiver to tell where the message ends
        which means even when the data is split over many packets
        or when many data is joined together in the buffer
        the program will always receive the data as a single, unbroken message.
     - Responses
        A handler can be attached, which will be called every time a complete message is received.
        the data received is provided as an argument to the handler
        and when the handler returns, its return value will be sent back to the sender
        (only if the sender needs it)
     - Callbacks
        A callback function can be supplied with each send_request.
        Once the request is fulfilled by the server and a response is received,
        the callback function will be called automatically.
     - Request Types
        Each request may optionally contain a request type field.
        A handler can be seperately attatched to each request type.
        This can be used to direct each request to an individial handler.

    '''
    def __init__(self, asyncsocket: async_socket.AsyncSocket):
        self._as = asyncsocket
        self._as.add_data_receive_callback(self._recv_handler)

        self._current_req_num = 0

        self._pending_callbacks = dict()
        self._handlers = dict()

        self._buffer = bytes()

    def _recv_handler(self, data):
        # Try to consume as many frames as possible
        self._buffer += data
        while self._try_parse():
            pass

    def _try_parse(self):
        # try to consume a frame
        try:
            spf,consumed=_SmartPipeFrame.frame_unpack(self._buffer)
            self._buffer = self._buffer[consumed:]
        except _IncompleteFrameException:
            return False
        print("SmartPipe received a complete frame.")
        print(perline_prefix(str(spf)," |"))

        if spf.is_response:
            self._pending_callbacks[spf.request_id](spf.payload)
            del self._pending_callbacks[spf.request_id]
        else:
            print(" > Handler called.")
            result = self._handlers[spf.request_type](spf.payload)
            if spf.response_expected:
                spf2=_SmartPipeFrame.frame_create(
                    payload=result,
                    response_expected=False,
                    is_response=True,
                    request_id=spf.request_id,
                    request_type=spf.request_type
                )
                print("SmartPipe is sending a response.")
                print(perline_prefix(str(spf2), " |"))
                self._as.send_data(_SmartPipeFrame.frame_pack(spf2))

        return True

    def kill_pipe(self):
        self._as.kill_socket()

    def send_request(self, data, rqtype=60000, callback_function=None):
        '''
        Send a request over the pipe.
        data: a bytes() object
        rqtype: the request type. should be an integer 1~60000
                if not set, defaults to 60000
        callback_function: Function to be called when the response is received.
                           is this is not set, it is assumed that the caller is not interested
                           in the response and the receiver will not send a response.
        '''

        self._current_req_num += 1

        spf=_SmartPipeFrame.frame_create(
            payload=data,
            response_expected=(callback_function is not None),
            is_response=False,
            request_id=self._current_req_num,
            request_type=rqtype
        )

        print("SmartPipe is sending data.")
        print(perline_prefix(str(spf), " |"))

        if callback_function is not None:
            self._pending_callbacks[self._current_req_num] = callback_function

        self._as.send_data(_SmartPipeFrame.frame_pack(spf))

        return self._current_req_num

    def cancel_callback(self, req_id):
        del self._pending_callbacks[req_id]

    def set_handler(self, handler,rqtype=None):
        '''
        Attach a handler.
        handler: a function taking in a single argument.
                 the argument is the data received.
                 the function may return a bytes() object, which will be sent back to the requester.
        rqtype: a request type this handler will attach to. integer 1~60000
                if not set, defaults to 60000
        '''
        if rqtype < 1 or rqtype > 60000:
            raise Exception("rqtype must be in range [1..60000]")
        self._handlers[rqtype] = handler
