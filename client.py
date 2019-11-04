import tkinter
import socket
import atexit

FPS = 30
PERIOD = 1 / FPS


def receive_packet():
    data = sock.recv(2048)
    protocol_number = int.from_bytes(data[:4], 'little');
    print(protocol_number)

    root.after(int(1000 * PERIOD), receive_packet)

    
def close_event():
    sock.close()


def set_name():
    pass


def get_users():
    pass

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
    root.after(int(1000 * PERIOD), receive_packet)
    root.mainloop()
