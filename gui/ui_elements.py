'''
Defines common UI Elements that will be used throughout the application.
'''

import tkinter
import tkinter.ttk
from data import client_data
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

        print("Loading", path, "with", len(files), "files")

        for filename in files:
            #print(filename)
            filepath=os.path.join(path,filename)
            self._data[filename]=tkinter.PhotoImage(file=filepath)
    @classmethod
    def _pidx_to_letter(cls,pidx):
        if pidx<1 or pidx>4:
            raise Exception("Invalid Player Index of "+str(pidx))
        return ["A","B","C","D"][pidx-1]
    def provide_sprite_for(self,cell):
        if cell.state == mines.CellState.locked:
            return self._data["nC.gif"]

        letter=self._pidx_to_letter(cell.owner)
        if cell.state == mines.CellState.clickable:
            return self._data[letter+"C.gif"]
        if cell.state==mines.CellState.clicked:
            if cell.is_mine:
                return self._data[letter+"M.gif"]
            return self._data["{}{}.gif".format(letter,cell.number)]
        if cell.state==mines.CellState.flagged:
            return self._data[letter+"F.gif"]
        raise Exception("sprite error")



class MineDisplay3(tkinter.Frame):
    '''
    A MineDisplay, for use with MineManager and the immutable mine data structures.
    '''
    def __init__(self,root,sprite_provider,mine_manager,*args,**kwargs):
        super().__init__(root,*args,**kwargs)
        self._canvas=tkinter.Canvas(self)
        self._sp=sprite_provider
        self._ss=sprite_provider.sprite_size()

        self._canvas.pack()
        self._canvas_ids=dict()

        self._mine_manager=mine_manager #MineFieldEventStack
        self._change_listener = lambda x: self._refresh_field()
        self._mine_manager.add_update_callback(self._change_listener)

        self._canvas.bind("<Button-1>", self._click_handler)
        self._canvas.bind("<ButtonRelease-1>", self._click_handler)
        self._canvas.bind("<Button-3>", self._click_handler)
        self._canvas.bind("<ButtonRelease-3>", self._click_handler)

        # Bit 0 (LSB) = LMB was clicked
        # Bit 1 = RMB was clicked
        self._current_click_type=0

        self._field_state_cache=None

        self._refresh_field()

    def _click_handler(self,evt):
        #print(evt.x,evt.y,evt.num,evt.type,type(evt.type))
        if evt.type==tkinter.EventType.ButtonPress:
            if evt.num==1:
                self._current_click_type |= 1
            elif evt.num==3:
                self._current_click_type |= 2
        elif evt.type==tkinter.EventType.ButtonRelease:
            if self._current_click_type==0:
                pass
            else:
                self._consume_click(evt.x,evt.y,self._current_click_type)
                self._current_click_type = 0
    def _consume_click(self,x,y,btn):
        rawcoords=(x,y)
        cellcoords=Tuples.element_wise_div(rawcoords,self._ss)
        cellintcoords=Tuples.floor(cellcoords)
        self._mine_manager.user_input(cellintcoords,btn)

    def _set_dimensions(self, x, y):
        self._all_delete()
        size = Tuples.element_wise_mult(self._ss,(x,y))
        self._canvas.configure(width=size[0],height=size[1])

    def _all_delete(self):
        for i in self._canvas_ids:
            self._canvas.delete(self._canvas_ids[i])
        self._canvas_ids=dict()

    def _refresh_field(self):
        old_state=self._field_state_cache
        new_state=self._mine_manager.get_state()
        self._field_state_cache=new_state

        if new_state is None:
            return

        cells_to_update=[]
        if (old_state is None) or (old_state.dimensions != new_state.dimensions):
            # dimensions changed - refresh everything
            self._set_dimensions(*(new_state.dimensions))
            cells_to_update=list(new_state.indices()) # every cell
        else:
            for coords in old_state:
                if old_state[coords] != new_state[coords]:
                    cells_to_update.append(coords)


        for coords in cells_to_update:
            self._refresh_single_cell(new_state, coords)


    def _refresh_single_cell(self, minefieldstate, coords):

        if coords in self._canvas_ids:
            self._canvas.delete(self._canvas_ids[coords])

        cell=minefieldstate[coords]
        bmp=self._sp.provide_sprite_for(cell)
        bmpsize=self._ss

        center_coords=Tuples.add(coords,(0.5,0.5))
        canvas_coords=Tuples.element_wise_mult(bmpsize,center_coords)
        objid=self._canvas.create_image(canvas_coords,image=bmp)
        self._canvas_ids[coords]=objid

import colorsys
def hsv(h,s,v):
    rgb=colorsys.hsv_to_rgb(h,s,v)
    return "#{:02x}{:02x}{:02x}".format(round(rgb[0]*255),round(rgb[1]*255),round(rgb[2]*255))
_status_display_color_scheme={
    1:hsv(0   ,0.3,0.9),
    2:hsv(0.25,0.3,0.9),
    3:hsv(0.50,0.3,0.9),
    4:hsv(0.75,0.3,0.9)
    }
class PlayerStatusDisplay(tkinter.Frame):
    def __init__(self,root,mine_manager,player_index,rtl=False,*args,**kwargs):
        super().__init__(root,*args,**kwargs)
        if rtl:
            col_index=10
        else:
            col_index=0
        def next_col_index():
            nonlocal col_index
            if rtl:
                col_index-=1
            else:
                col_index+=1
            return col_index
        self._mm=mine_manager
        self._pidx=player_index
        bgcolor=_status_display_color_scheme[player_index]
        print(bgcolor)


        self._index_display=tkinter.Label(self,text="Player {}".format(player_index))
        self._index_display.grid(row=1,column=next_col_index())

        self._score_display_VAR=tkinter.StringVar()
        self._score_display=tkinter.Label(self,textvariable=self._score_display_VAR)
        self._score_display.grid(row=1,column=next_col_index())

        self.configure(background=bgcolor)
        self._score_display.configure(background=bgcolor)
        self._index_display.configure(background=bgcolor)


        # TODO this is a memory leak - refernece will still be held after this widget is destryoed
        self._mm.add_update_callback(lambda dat:self._mm_update_handler())

    def _mm_update_handler(self):
        scores=self._mm.get_score()
        pidx=self._pidx
        if pidx in scores:
            self.update_score(scores[pidx])
        else:
            self.update_score(0)

    def update_score(self,score):
        self._score_display_VAR.set(str(score))


def main3():
    root = tkinter.Tk()
    mm=mines.MineManager(1)

    md = MineDisplay3(root,DefaultSpriteProvider("sprites/",(16,16)),mm)
    md.pack()

    mfs = mines.MineFieldGenerator.generate_symmetrical(50, 25, 0.15)
    mm.server_sync(mfs)

    pidx=1
    def btncmd():
        nonlocal pidx
        pidx=(pidx)%2+1
        mm.debug_change_pidx(pidx)
        btn.configure(text="On side: {}".format(pidx))
    btn=tkinter.Button(root,text="Switch sides",command=btncmd)
    btn.pack()


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
    main3()
