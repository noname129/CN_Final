
'''
A wrapper directly on top of sockets.
Abstracts away the socket creation / thread management / blocking reads.
Allows programs to use sockets as an asynchronous data pipe.

start_server(new_connection_handler, host, port)
    starts a 'server' where clients can connect to.
    host,port : socket parameters
    new_connection_handler: a callback function. will be called when a client connects to this server.
                            the AsyncSocket instance from that connection will be provided as an argument.

initiate_connection()
    connects to a host that has start_server() running. Returns a AsyncSocket.

For using the AsyncSocket class itself, refer to its own docstring.
'''
import threading
import socket

class AsyncSocket:
    '''
    It's like a socket, but asynchronous.
    There are 4 actions you can take with an instance of this class:
     - send_data(data)
       Send a bytes() object through the socket.
     - add_data_receive_callback(callback)
       Register a callback to be called every time this socket receives new data
     - add_connection_error_callback(callback)
       Register a callback to be called when an error occurs.
     - add_connection_close_callback(callback)
       Register a callback to be called when this socket dies.
    '''
    def __init__(self, sock, addr, port):
        print("AsyncSocket initialized:",addr,port)
        self._addr=addr
        self._port=port
        self._sock=sock
        self._recv_callbacks=[]
        self._error_callbacks=[]
        self._close_callbacks=[]


    def add_data_receive_callback(self, cb):
        self._recv_callbacks.append(cb)
    def remove_data_receive_callback(self,cb):
        self._recv_callbacks.remove(cb)

    def add_connection_error_callback(self, cb):
        self._error_callbacks.append(cb)

    def add_connection_close_callback(self, cb):
        self._close_callbacks.append(cb)

    def _call_error_callbacks(self, err):
        for i in self._error_callbacks:
            i(err)

    def _call_recv_callbacks(self,data):
        '''
        print("AsyncSocket received data")
        print(" |From:",self._addr,self._port)
        dat = str(data)
        if len(dat) > 250:
            dat = "(blob, {} bytes)".format(len(dat))
        print(" |Data: " + dat)'''

        for i in self._recv_callbacks:
            i(data)

    def _call_close_callbacks(self):
        for i in self._close_callbacks:
            i()

    def kill_socket(self):
        self._sock.close()

    def send_data(self, data):
        '''
        print("AsyncSocket is sending data")
        print(" |To:", self._addr, self._port)
        dat=str(data)
        if len(dat)>250:
            dat="(blob, {} bytes)".format(len(dat))
        print(" |Data: " + dat)'''

        self._sock.sendall(data)

    def _threading_loop(self):
        # Should only be called by _start_blob_pipe()
        try:
            while True:
                data = self._sock.recv(4096)

                if len(data) == 0:
                    break

                self._call_recv_callbacks(data)

        except ConnectionAbortedError:
            # Normal termination
            pass

        except ConnectionError as err:
            print('Error occurred: ', err)
            self._call_error_callbacks(err)

        self._call_close_callbacks()
        print("Closing AsyncSocket")
        self._sock.close()

def _start_blob_pipe(sock, addr, port):
    lc=AsyncSocket(sock, addr, port)
    threading.Thread(
        target=lambda:lc._threading_loop()
    ).start()
    return lc

def _accept_connections(handler, host, port):
    threading.Thread(
        target=lambda :_connection_listen_loop(handler,host,port)
    ).start()

def _connection_listen_loop(handler, host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        print("Bind to...",host,port)
        sock.bind((host, port))

        sock.listen()

        while True:
            (client_sock, (ip, port)) = sock.accept()
            lc=_start_blob_pipe(client_sock, ip, port)
            handler(lc)

_started=False
def start_server(new_connection_handler, host, port):
    global _started
    if _started:
        raise Exception("Cannot start twice!")
    _started=True

    _accept_connections(new_connection_handler,host,port)

def initiate_connection(ip,port):
    s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip,port))

    return _start_blob_pipe(s, ip, port)