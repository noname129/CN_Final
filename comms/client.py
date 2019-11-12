import tkinter
import socket
import threading
import atexit
from comms.common import *



def process_packet(data):
    protocol_number = int.from_bytes(data[:4], 'little');
    print('Receive packet type', protocol_number)

    if protocol_number == GET_USER_LIST_RESPONSE:
        user_count = int.from_bytes(data[4:8], 'little')
        res = struct.unpack(GetUserListResponse.var_fmt(user_count), data)
        for i in range(2, user_count + 2):
            print(res[i].decode('utf-8'))


def receive_packet():
    while True:
        data = sock.recv(2048)
        process_packet(data)

    
def close_event():
    sock.close()


def set_name():
    sock.send(create_packet(SetUserNameRequest(textbox.get())))


def get_users():
    sock.send(create_packet(GetUserListRequest()))


if __name__ == '__main__':
    ip, port = input('IP:'), int(input('Port:'))
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ip, port))
    atexit.register(close_event)

    root = tkinter.Tk()

    textbox = tkinter.Entry(root)
    textbox.pack()
    btn_set_name = tkinter.Button(root, text='set name', command=set_name)
    btn_set_name.pack()
    btn_get_users = tkinter.Button(root, text='print all users', command=get_users)
    btn_get_users.pack()


    # root.protocol('WM_DELETE_WINDOW', close_window_event)
    receiver = threading.Thread(target=receive_packet)
    receiver.start()
    root.mainloop()
