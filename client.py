import tkinter

FPS = 30
PERIOD = 1 / FPS


def recieve_packet():
    
    root.after(PERIOD, recieve_packet)

    
def close_window_event():
    sock.close()


if __name__ == '__main__':
    ip, port = input('IP:'), port = int(input('Port:'))
    sock = socket.socket(socket.AF_INET, sock.SOCK_STREAM)
    sock.connect((ip, port))


    root = tkinter.Tk()
    root.protocol('WM_DELETE_WINDOW', close_window_event)
    recieve_packet()
    root.mainloop()
