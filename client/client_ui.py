'''
Actual UI design & definition
'''
import tkinter.ttk
import tkinter.messagebox
from client import ui_elements
import time
from util.utils import *
from util.tk_utils import *
from api import client_api
from api import api_datatypes
from client import client_logic

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

# Functions to be ran when the tk terminates.
_efunc=[]
def add_exit_handler(func):
    _efunc.append(func)

def _run_exit_handlers():
    for i in _efunc:
        i()



def start(*,first_window_function=(lambda : _display_connect())):
    '''
    Entry point.
    invoke this function to display the client UI.
    '''
    print('UI: Start')
    global _tk
    _tk = tkinter.Tk()
    _tk.withdraw()

    _tk.after_idle(first_window_function)
    _tk.after_idle(_periodic_100)
    _tk.mainloop()


def _display_connect():
    print("UI: display connect")
    root=tkinter.Toplevel()
    root.title("SWEEPERS Server Connect")
    root.protocol("WM_DELETE_WINDOW", _window_close_handler)

    root.columnconfigure(2, weight=1)

    label = tkinter.Label(root, text="SWEEPERS")
    label.grid(row=1, column=1, columnspan=2, sticky=tk_all_directions)


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

    loginbtn = tkinter.Button(root, text="Connect")
    loginbtn.grid(row=6, column=1, columnspan=2, sticky=tk_all_directions)


    def login_callback():
        ip = addr_input_VAR.get()
        port = int(port_input_VAR.get())
        clicon=client_api.ClientSideAPI(
            ip,port,
            _tk
        )

        add_exit_handler(lambda:clicon.kill_connection())

        root.destroy()
        _display_login(clicon)

    loginbtn.configure(command=login_callback)

def _display_login(clicon:client_api.ClientSideAPI):
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


    loginbtn = tkinter.Button(root, text="Log in")
    loginbtn.grid(row=6, column=1, columnspan=2, sticky=tk_all_directions)

    def success_ui_apply(player_id):
        cs = client_logic.ClientState()
        cs.set_player_id(player_id)
        root.destroy()
        _display_lobby(clicon, cs)

    def success_callback(player_id):
        success_ui_apply(player_id)


    def fail_callback(msg):
        tkinter.messagebox.showerror("Error", msg)

    def login_callback():
        clicon.login(
            name_input_VAR.get(),
            success_callback,fail_callback
        )

    loginbtn.configure(command=login_callback)


def _display_lobby(clicon:client_api.ClientSideAPI, cstate:client_logic.ClientState):
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

    createbtn = tkinter.Button(root, text="Create room")
    createbtn.grid(row=4, column=1, sticky=tk_all_directions)

    def refresh_success_ui_apply(data):
        lobbydisplay.new_data(data)

    def refresh_success(data):
        refresh_success_ui_apply(data)

    def refresh():
        clicon.fetch_game_list(
            refresh_success
        )

    refreshbtn.configure(command=refresh)

    refresh()

    def join_success(room_id, player_index):
        cigl = client_logic.ClientInGameLogic(clicon, player_index, room_id)
        root.destroy()
        _display_game(clicon, cstate, cigl)

    def join_fail(msg):
        tkinter.messagebox.showerror("Error", msg)

    def join():
        gi = lobbydisplay.get_selection()
        if gi is None:
            tkinter.messagebox.showerror("Error", "Select a game first")
            return
        clicon.join_game(cstate.player_id, gi.room_id, join_success, join_fail)

    joinbtn.configure(command=join)

    def create_success(room_id):
        refresh()
        clicon.join_game(cstate.player_id, room_id, join_success, join_fail)

    createbtn.configure(command=lambda:_display_room_creation(clicon,create_success))


def _display_room_creation(clicon:client_api.ClientSideAPI, success_cb):
    print("UI: roomcreate")
    root = tkinter.Toplevel()
    root.title("SWEEPERS game create")

    root.columnconfigure(2,weight=1)

    players_label=tkinter.Label(root,text="Number of players")
    players_label.grid(row=1, column=1)


    xy_sync=False
    def players_radiobutton_FUNC():
        nonlocal xy_sync
        val=players_radiobutton_VAR.get()
        xy_sync=(val=="4")
        if xy_sync:
            fieldsize_spinbox_y_VAR.set(
                fieldsize_spinbox_x_VAR.get()
            )
    players_radiobutton=tkinter.Frame(root)
    players_radiobutton_VAR=tkinter.StringVar()
    # INTERNAL BUG IN TKINTER
    # Below set() should make the radiobutton select the first button but doesn't.
    # However, inserting below code
    # root.after(10000, lambda: print(players_radiobutton_VAR.get()))
    # here makes it work for some reason.
    # Windows 10, win32, python 3.7.2
    players_radiobutton_VAR.set(2)
    players_radiobutton_2=tkinter.Radiobutton(players_radiobutton,
                                              text="2",
                                              variable=players_radiobutton_VAR,
                                              value=2,
                                              command=players_radiobutton_FUNC)
    players_radiobutton_2.grid(column=1,row=1)
    players_radiobutton_4 = tkinter.Radiobutton(players_radiobutton,
                                                text="4",
                                                variable=players_radiobutton_VAR,
                                                value=4,
                                                command=players_radiobutton_FUNC)
    players_radiobutton_4.grid(column=2,row=1)
    players_radiobutton.grid(row=1,column=2)


    name_label=tkinter.Label(root,text="Name")
    name_label.grid(row=2,column=1)

    name_input_VAR=tkinter.StringVar()
    name_input=tkinter.Entry(root,textvariable=name_input_VAR)
    name_input.grid(row=2,column=2)

    fieldsize_label=tkinter.Label(root,text="Field Size")
    fieldsize_label.grid(row=3,column=1)

    fieldsize_spinboxes=tkinter.Frame(root)
    fieldsize_spinbox_x_VAR=tkinter.StringVar()
    fieldsize_spinbox_x_VAR.set(40)
    def fieldsize_spinbox_x_CMD():
        if xy_sync:
            fieldsize_spinbox_y_VAR.set(
                fieldsize_spinbox_x_VAR.get()
            )
    fieldsize_spinbox_x=tkinter.Spinbox(fieldsize_spinboxes,
                                        from_=10,
                                        to=80,
                                        textvariable=fieldsize_spinbox_x_VAR,
                                        command=fieldsize_spinbox_x_CMD)
    fieldsize_spinbox_x.grid(row=1,column=1)
    fieldsize_spinbox_y_VAR = tkinter.StringVar()
    fieldsize_spinbox_y_VAR.set(20)
    def fieldsize_spinbox_y_CMD():
        if xy_sync:
            fieldsize_spinbox_x_VAR.set(
                fieldsize_spinbox_y_VAR.get()
            )
    fieldsize_spinbox_y = tkinter.Spinbox(fieldsize_spinboxes,
                                          from_=5,
                                          to=60,
                                          textvariable=fieldsize_spinbox_y_VAR,
                                          command=fieldsize_spinbox_y_CMD)
    fieldsize_spinbox_y.grid(row=1, column=3)
    tkinter.Label(fieldsize_spinboxes,text=" x ").grid(row=1,column=2)
    fieldsize_spinboxes.grid(row=3,column=2)

    mineprob_label=tkinter.Label(root,text="Mine Probability")
    mineprob_label.grid(row=4,column=1)

    mineprob_slider=tkinter.Frame(root)
    def mineprob_slider_get():
        return mineprob_slider_scale.get()/1000*15+5
    def mineprob_slider_scale_cmd(evt):
        val=mineprob_slider_get()
        mineprob_slider_disp_VAR.set("{:4.1f}%".format(val))
    mineprob_slider_scale=tkinter.Scale(mineprob_slider,
                                        orient=tkinter.HORIZONTAL,
                                        from_=0,to=1000,
                                        command=mineprob_slider_scale_cmd,
                                        showvalue=0,
                                        length=250)
    mineprob_slider_scale.grid(row=1,column=1)
    mineprob_slider_scale.set(300)
    mineprob_slider_disp_VAR=tkinter.StringVar()
    mineprob_slider_disp=tkinter.Label(mineprob_slider,textvariable=mineprob_slider_disp_VAR)
    mineprob_slider_disp.grid(row=1,column=2)
    mineprob_slider.grid(row=4,column=2)

    create_btn=tkinter.Button(root,text="Create")
    create_btn.grid(row=5,column=1,columnspan=2)


    def create_success(room_id):
        success_cb(room_id)
        root.destroy()

    def create_fail(msg):
        tkinter.messagebox.showerror("Error", msg)

    def send_create_req():

        grp=api_datatypes.RoomCreationParameters(
            max_players=int(players_radiobutton_VAR.get()),
            name=name_input_VAR.get(),
            field_size_x=int(fieldsize_spinbox_x_VAR.get()),
            field_size_y=int(fieldsize_spinbox_y_VAR.get()),
            mine_prob=mineprob_slider_get()
        )
        #print(grp)
        clicon.create_game(grp, create_success, create_fail)
    create_btn.configure(command=send_create_req)








def _display_game(clicon:client_api.ClientSideAPI,
                  cstate:client_logic.ClientState,
                  clogic:client_logic.ClientInGameLogic):
    # TODO implement 4-player - right now this only handles 2-player.
    print("UI: game")
    root = tkinter.Toplevel()
    root.title("SWEEPERS game")
    root.protocol("WM_DELETE_WINDOW", _window_close_handler)

    root.columnconfigure(2,weight=1)
    minedisplay= ui_elements.MineDisplay3(root, ui_elements.DefaultSpriteProvider("sprites/", (16, 16)), clogic)

    minedisplay.grid(row=2,column=1,columnspan=3)

    p1_psd= ui_elements.PlayerStatusDisplay(root, clogic, 1)
    p1_psd.grid(row=1,column=1)

    p2_psd = ui_elements.PlayerStatusDisplay(root, clogic, 2)
    p2_psd.grid(row=1, column=3)

    p3_psd = ui_elements.PlayerStatusDisplay(root, clogic, 3)
    p3_psd.grid(row=3, column=1)

    p4_psd = ui_elements.PlayerStatusDisplay(root, clogic, 4)
    p4_psd.grid(row=3, column=3)


    def refresh(igrp):
        pass
    clogic.add_room_update_callbaks(refresh)
    clogic.fetch_room_params()

    clicon.ingame_explicit_newstate_request(cstate.player_id)



def _window_close_handler():
    print("Game killed")
    _run_exit_handlers()
    _tk.destroy()

def main():

    pass


if __name__=="__main__":
    main()