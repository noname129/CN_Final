'''
Defines common UI Elements that will be used throughout the application.
'''

import tkinter
import tkinter.ttk
from data import client_data
import random
from util import multiarray
from game import mines

from util.utils import tk_all_directions
from util.utils import Tuples


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

# random hex color
def _rand_color():
    return "#{:02x}{:02x}{:02x}".format(
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255)
    )


class MineDisplay(tkinter.Frame):
    '''
    A tkinter-compatible child of Frame that can be inserted into any Tk widget.
    Takes in a Minefield object and displays it graphically.
    Note that this uses a single internal Frame for every cell; expect poor performance for large fields.
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._frames = multiarray.MultiDimArray()
        self._minefield = None
        self._change_listener = lambda coords: self._refresh_cell(coords)

    def set_minefield(self, mf):
        '''
        Link this widget to a MineField object.
        Once linked, this widget will update as the Minefield object gets updated,
        and will send click events to the Minefield object.
        '''

        # remove reference from previous minefield
        if self._minefield is not None:
            self._minefield.remove_change_listener(self._change_listener)

        self._minefield = mf
        self._set_dimensions(mf.x, mf.y)
        self._refresh_cell(None)

        # event listener
        self._minefield.add_change_listener(self._change_listener)

    def _set_dimensions(self, x, y):
        # Set dimensions - delete everything and start from scratch
        for i in self._frames:
            self._frames[i].grid_forget()
            self._frames[i].destroy()

        # Again, frames are stored in a MultiDimArray.
        self._frames = multiarray.MultiDimArray(x, y)

        for xi in range(x):
            for yi in range(y):
                frame = tkinter.Label(self,
                                      width=2, height=1,
                                      background=_rand_color() # this line can be removed
                                      )

                # Note that the click handlers are actually generated from a function in a awkward fashion.
                # If you define a lambda function right here, the values of xi and yi will get updated with the loop
                # therefore a detour was needed
                frame.bind("<Button-1>", self._lmb_handler_generator(xi, yi))
                frame.bind("<Button-3>", self._rmb_handler_generator(xi, yi))

                frame.grid(column=xi, row=yi)
                self._frames[xi, yi] = frame

    def _lmb_handler_generator(self, x, y):
        # Left Mouse Button handler
        return lambda evt: self._click_handler((x, y), 1)

    def _rmb_handler_generator(self, x, y):
        # Right Mouse Button handler
        return lambda evt: self._click_handler((x, y), 2)

    def _click_handler(self, coords, button):
        # Click handler that actually sends events to the minefield object
        if self._minefield is not None:
            self._minefield.click(coords, button)

    @classmethod
    def _stylize(cls, frame, cell):
        # This method is the one that actually styles the individual cells.
        # Subclasses can override this function to get a different look
        if cell.state == mines.CellState.hidden:
            frame.configure(background="#404040")
        elif cell.state == mines.CellState.flagged:
            frame.configure(background="#FF0000")
        elif cell.state == mines.CellState.uncovered:
            frame.configure(background="#FFFFFF",
                            text=str(cell.number))

    def _refresh_cell(self, coords):
        # Refresh, or re-stylize a cell.
        if self._minefield is None:
            return
        if coords is None:
            for coords in self._minefield:
                self._refresh_cell(coords)
        self._stylize(self._frames[coords], self._minefield[coords])


class SpriteProvider():
    def sprite_size(self):
        raise NotImplementedError
    def provide_sprite_for(self,cell):
        raise NotImplementedError

import os
import os.path
class DefaultSpriteProvider(SpriteProvider):
    def __init__(self,path,ss,*args,**kwargs):
        super().__init__(*args,**kwargs)

        self._data=dict()
        self._ss=ss

        self._load(path)
    def sprite_size(self):
        return self._ss
    def _load(self,path):

        files=os.listdir(path)

        #print("Loading", path, "with", len(files), "files")

        for filename in files:
            print(filename)
            filepath=os.path.join(path,filename)
            self._data[filename]=tkinter.PhotoImage(file=filepath)
    def provide_sprite_for(self,cell):
        if cell.state == mines.CellState.locked:
            return self._data["nC.gif"]
        if cell.state == mines.CellState.clickable:
            return self._data["AC.gif"]
        if cell.state==mines.CellState.clicked:
            return self._data["A{}.gif".format(cell.number)]
        if cell.state==mines.CellState.flagged:
            return self._data["AF.gif"]
        raise Exception("sprite error")


class MineDisplay2(tkinter.Frame):
    def __init__(self,root,sprite_provider,*args,**kwargs):
        super().__init__(root,*args,**kwargs)
        self._canvas=tkinter.Canvas(self)
        self._sp=sprite_provider
        self._ss=sprite_provider.sprite_size()

        self._canvas.pack()
        self._canvas_ids=dict()

        self._minefield=None
        self._change_listener = lambda coords: self._refresh_cell(coords)

        self._canvas.bind("<Button-1>", self._click_handler)
        self._canvas.bind("<Button-3>", self._click_handler)

    def _click_handler(self,evt):
        #print(evt.num)
        rawcoords=(evt.x,evt.y)
        #print(rawcoords)
        cellcoords=Tuples.element_wise_div(rawcoords,self._ss)
        cellintcoords=Tuples.floor(cellcoords)
        #print(cellintcoords)
        if self._minefield is not None:
            if evt.num==1:
                btn=1
            elif evt.num==3:
                btn=2
            else:
                return
            self._minefield.click(cellintcoords,btn)
    def set_minefield(self,mf):
        # remove reference from previous minefield
        if self._minefield is not None:
            self._minefield.remove_change_listener(self._change_listener)

        self._minefield = mf
        self._set_dimensions(mf.x, mf.y)
        self._refresh_cell(None)

        # event listener
        self._minefield.add_change_listener(self._change_listener)

    def _set_dimensions(self, x, y):
        self._all_delete()
        size = Tuples.element_wise_mult(self._ss,(x,y))
        self._canvas.configure(width=size[0],height=size[1])
    def _all_delete(self):
        for i in self._canvas_ids:
            self._canvas.delete(self._canvas_ids[i])
        self._canvas_ids=dict()

    def _refresh_cell(self, coords):
        print("mf2 refresh",coords)
        if self._minefield is None:
            return
        if coords is None:
            for coords in self._minefield:
                self._refresh_cell(coords)

        if coords in self._canvas_ids:
            self._canvas.delete(self._canvas_ids[coords])

        cell=self._minefield[coords]
        bmp=self._sp.provide_sprite_for(cell)
        bmpsize=self._ss

        center_coords=Tuples.add(coords,(0.5,0.5))
        canvas_coords=Tuples.element_wise_mult(bmpsize,center_coords)
        objid=self._canvas.create_image(canvas_coords,image=bmp)
        self._canvas_ids[coords]=objid

def main():
    root = tkinter.Tk()

    md = MineDisplay2(root,DefaultSpriteProvider("sprites/",(12,12)))
    md.pack()

    mf = mines.MineField.generate_symmetrical(140, 80, 0.05)
    md.set_minefield(mf)

    root.mainloop()


def main2():
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
