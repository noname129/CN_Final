'''
Actual UI design & definition
'''

import tkinter
import tkinter.messagebox
import ui_elements
import time
from utils import *
import client

# The almighty root window
_tk = None


# Some functions for defining custom recurring events
# Not used yet but may come handy later
_rfunc = []
class RecurringFunction:
    def __init__(self, func, hz):
        self._func = func
        self._interval = 1 / hz
        self._time_elapsed = 0

    def tick(self, elapsed):
        self._time_elapsed += elapsed
        if self._time_elapsed > self._interval:
            self._func()
            self._time_elapsed = 0
_last_run = None
def _periodic_100():
    global _last_run
    current_time = time.time()
    if _last_run is None:
        _last_run = current_time
    delta_time = current_time - _last_run
    current_time = delta_time

    for rf in _rfunc:
        rf.tick(delta_time)
    _tk.after(10, _periodic_100)
def add_recurring(func, hz):
    _rfunc.append(RecurringFunction(func, hz))



def start():
    '''
    Entry point.
    invoke this function to display the client UI.
    '''
    print('UI: Start')
    global _tk
    _tk = tkinter.Tk()
    _tk.withdraw()

    _tk.after(0, _display_login)
    _tk.after(0, _periodic_100)
    _tk.mainloop()


def _display_login():
    print("UI: display login")
    root = tkinter.Toplevel()
    root.title("SWEEPERS login")
    root.protocol("WM_DELETE_WINDOW", _window_close_handler)

    root.columnconfigure(2, weight=1)

    label = tkinter.Label(root, text="SWEEPERS")
    label.grid(row=1, column=1, columnspan=2, sticky=tk_all_directions)

    name_label = tkinter.Label(root, text="Username")
    name_label.grid(row=2, column=1, sticky=tk_all_directions)
    name_input_VAR = tkinter.StringVar()
    name_input = tkinter.Entry(root, textvariable=name_input_VAR)
    name_input.grid(row=2, column=2, sticky=tk_all_directions)

    addr_label = tkinter.Label(root, text="Server IP / URL")
    addr_label.grid(row=3, column=1, sticky=tk_all_directions)
    addr_input_VAR = tkinter.StringVar()
    addr_input_VAR.set("localhost")
    addr_input = tkinter.Entry(root, textvariable=addr_input_VAR)
    addr_input.grid(row=3, column=2, sticky=tk_all_directions)

    port_label = tkinter.Label(root, text="Server Port")
    port_label.grid(row=4, column=1, sticky=tk_all_directions)
    port_input_VAR = tkinter.StringVar()
    port_input_VAR.set("19477")
    port_input = tkinter.Entry(root, textvariable=port_input_VAR)
    port_input.grid(row=4, column=2, sticky=tk_all_directions)

    infostrip = tkinter.Label(root, text="")
    infostrip.grid(row=5, column=1, columnspan=2, sticky=tk_all_directions)

    loginbtn = tkinter.Button(root, text="Connect")
    loginbtn.grid(row=6, column=1, columnspan=2, sticky=tk_all_directions)

    def success_callback():
        root.destroy()
        _display_lobby()

    def fail_callback(msg):
        tkinter.messagebox.showerror("Error", msg)

    def login_callback():
        name = name_input_VAR.get()
        ip = addr_input_VAR.get()
        port = port_input_VAR.get()
        client.login(
            ip, port, name,
            success_callback, fail_callback
        )

    loginbtn.configure(command=login_callback)


def _display_lobby():
    print("UI: lobby")
    root = tkinter.Toplevel()
    root.title("SWEEPERS lobby")
    root.protocol("WM_DELETE_WINDOW", _window_close_handler)

    root.columnconfigure(1, weight=1)
    root.rowconfigure(2, weight=1)

    refreshbtn = tkinter.Button(root, text="Refresh")
    refreshbtn.grid(row=1, column=1, sticky=tk_all_directions)

    lobbydisplay = ui_elements.LobbyDisplay(root)
    lobbydisplay.grid(row=2, column=1, sticky=tk_all_directions)

    joinbtn = tkinter.Button(root, text="Join")
    joinbtn.grid(row=3, column=1, sticky=tk_all_directions)

    def refresh_success(data):
        lobbydisplay.new_data(data)

    def refresh_fail(msg):
        tkinter.messagebox.showerror("Error", msg)

    def refresh():
        client.fetch_game_list(
            refresh_success,
            refresh_fail
        )

    refreshbtn.configure(command=refresh)

    refresh()

    def join_success(gi):
        root.destroy()
        _display_game(gi)

    def join_fail(msg):
        tkinter.messagebox.showerror("Error", msg)

    def join():
        gi = lobbydisplay.get_selection()
        if gi is None:
            tkinter.messagebox.showerror("Error", "Select a game first you doofus")
            return
        client.join_game(gi.instance_id, join_success, join_fail)

    joinbtn.configure(command=join)


def _display_game(gi):
    # TODO implement
    print("UI: game")
    root = tkinter.Toplevel()
    root.title("SWEEPERS game")
    root.protocol("WM_DELETE_WINDOW", _window_close_handler)


def kill():
    _tk.destroy()


def _window_close_handler():
    print("Game killed")
    kill()
