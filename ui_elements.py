'''
Defines UI Elements that will be used throughout the application.
'''

import tkinter
import tkinter.ttk
import client_data

from utils import tk_all_directions


class LobbyDisplay(tkinter.Frame):
    '''
    Widget for displaying a list of client_data.GameInstances
    use new_data() to feed it data.
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        columns = ("Name", "open", "players", "field")
        self._treeview = tkinter.ttk.Treeview(
            self,
            columns=columns,
            show="headings"
        )
        for column in columns:
            self._treeview.heading(column, text=column)
        self._treeview.column(1, width=50)

        self._treeview.grid(row=1, column=1, sticky=tk_all_directions)

        self._map = dict()

        self.update()

    def _delete_all(self):
        for key in self._map:
            self._treeview.delete(key)
        self._map = dict()

    def _insert(self, gl):
        values = (gl.name,
                  ["CLOSED", "OPEN"][gl.joinable],
                  "{}/{}".format(len(gl.players), gl.max_players),
                  "{}x{} @{:.0f}%".format(gl.field_size[0], gl.field_size[1], gl.mine_prob * 100))
        iid = self._treeview.insert("", tkinter.END, values=values)
        self._map[iid] = gl

    def new_data(self, gamelisting_list):
        self._delete_all()

        gls = sorted(gamelisting_list, key=lambda gl: gl.name)

        for gl in gls:
            self._insert(gl)

    def get_selection(self):
        selsctions = self._treeview.selection()
        # print(selsctions)
        if selsctions:
            return self._map[selsctions[0]]
        else:
            return None


def main():
    tk = tkinter.Tk()
    ld2 = LobbyDisplay(tk)
    ld2.pack()

    def btncmd():
        # print(ld2.get_selection().instance_id)
        ld2.new_data([client_data.GameInstance()])

    btn = tkinter.Button(tk, text="db", command=btncmd)
    btn.pack()

    tk.mainloop()


if __name__ == "__main__":
    main()
