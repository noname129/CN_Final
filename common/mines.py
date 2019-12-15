import enum
from util.utils import Tuples
import util.utils
import random
from util import multiarray
import collections

_neighbor_deltas = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))

class CellState:
    '''
    Enum of possible cell states
    '''
    locked = 0
    clickable=1
    clicked = 2
    flagged = 3


class ImmutableCell():
    '''
    Class representing a single cell. Immutable!

    state:   locked/clickable/cliucked/flagged
    owner:   for clicked / flagged cells, this is the player index that clicked the cell.
             for clickable cells, this is the player index that can click the cell.
    is_mine: is this a mine?
    number:  Number of adjacent mines
    '''
    def __init__(self, state, owner, is_mine, number):
        self._state=state
        self._owner=owner
        self._is_mine=is_mine
        self._number=number

        if not self._check_attribute_types():
            raise Exception("Invalid cell! "+str(self))


    def __eq__(self, other):
        return ((self._state == other._state) and
                (self._owner == other._owner) and
                (self._is_mine == other._is_mine) and
                (self._number == other._number))

    def __ne__(self,other):
        return not self.__eq__(other)

    def __repr__(self):
        return "ImmutableCell({},{},{},{})".format(self.state,self.owner,self.is_mine,self.number)

    def can_click_by(self,player_index):
        if self.state==CellState.locked:
            return False # Can't modify locked cells
        elif self.state==CellState.clicked:
            return False # Can't modify a cell that's already clicked
        elif self.state==CellState.flagged:
            return False # you already put a flag there
        else: #clickable state
            return self.owner==player_index

    @property
    def state(self):
        return self._state
    @property
    def owner(self):
        return self._owner
    @property
    def is_mine(self):
        return self._is_mine
    @property
    def number(self):
        return self._number

    @classmethod
    def from_cell(cls,cell):
        return ImmutableCell(
            state=cell.state,
            owner=cell.owner,
            is_mine=cell.is_mine,
            number=cell.number
        )

    def _check_attribute_types(self):
        if (type(self.state)==int
            and (0<=self.state<=3)
            and type(self.owner)==int
            and (0<=self.owner<=7)
            and type(self.is_mine) == bool
            and type(self._number)==int
            and 0<=self.number<=8):
            return True
        return False

    def to_bytes(self):
        byte1=0
        byte1 |= self.state # bits 0,1
        byte1 |= self.owner << 2 # bits 2,3,4
        byte1 |= self.is_mine << 5 # bit 5

        byte2=self.number # bits 0,1,2,3

        return bytes((byte1,byte2))

    @classmethod
    def from_bytes(cls, b):
        byte1=b[0]
        byte2=b[1]
        state = byte1 & 3
        owner = (byte1 >> 2) & 7
        is_mine = ((byte1>>5) & 1) != 0
        number = byte2 & 15

        return ImmutableCell(
            state=state,
            owner=owner,
            is_mine=is_mine,
            number=number
        )

    def modify(self, state=None, owner=None, is_mine=None, number=None):
        if state is None:
            state=self._state
        if owner is None:
            owner=self._owner
        if is_mine is None:
            is_mine=self._is_mine
        if number is None:
            number=self._number
        return ImmutableCell(state,owner,is_mine,number)

    def score(self):
        '''
        return a score for this cell
        returns: (player_index, score)
                 or None
        '''
        if self.state==CellState.clicked:
            if self.is_mine: # kaboom!
                return (self.owner,-200)
            elif self.number==0: # blank
                pass
            else:
                return (self.owner,10)
        elif self.state==CellState.flagged:
            # No, wait. this is a terrible idea.
            #return (self.owner,30)
            pass


# Stores user input for "playback"
# x,y= int (0~)
# button = int (1~3)
# player_index = int (1~4)
MineFieldInput=collections.namedtuple("MineFieldInput",
                                      ("x","y","button","player_index"))


class MineFieldState:
    '''
    An IMMUTABLE minefield; a 2d grid of ImmutableCells.
    There are two main ways of initializing a MineFieldState:
      - Converting from MineField
      - Applying MineFieldInputs to existing MineFieldState
    '''

    @classmethod
    def to_bytes(cls, mfs):
        result=bytes()
        result += int(mfs.x).to_bytes(2,"big")
        result += int(mfs.y).to_bytes(2, "big")

        cell_data_bytes=bytearray()
        for coords in mfs:
            cell_data_bytes.extend(mfs[coords].to_bytes())
        result += bytes(cell_data_bytes)

        return result

    @classmethod
    def from_bytes(cls, b):
        x=int.from_bytes(b[0:2],"big")
        y=int.from_bytes(b[2:4],"big")
        cell_data=b[4:]
        if len(cell_data) != x*y*2:
            raise Exception("Only {} data in a {}x{} board?".format(len(cell_data),x,y))
        data=util.multiarray.MultiDimArray(x,y)
        idx=0
        for coords in data:
            data[coords]=ImmutableCell.from_bytes(cell_data[idx:idx+2])
            idx+=2

        return MineFieldState(data)



    @classmethod
    def from_minefield(cls,mf):
        imdata=multiarray.MultiDimArray(mf.x,mf.y)

        for coords in mf:
            orig_cell=mf[coords]
            imcell=ImmutableCell.from_cell(orig_cell)
            imdata[coords]=imcell

        return MineFieldState(imdata)

    def __init__(self,data):
        '''
        Initialize a minefield from a MultiDimArray of ImmutableCells
        '''
        self._data=data

    @property
    def dimensions(self):
        return self._data.dimensions
    @property
    def x(self):
        return self._data.x
    @property
    def y(self):
        return self._data.y

    def __iter__(self):
        return self._data.__iter__()
    def indices(self):
        return self._data.indices()
    def __getitem__(self,key):
        return self._data.__getitem__(key)

    def process_input(self,mfi):
        '''
        Processes user input defined by MineFieldInput mfi
        then returns a new MineFieldState object that results from that input.
        '''
        newdata=self._data.shallow_copy()

        if mfi.button==1:
            self._uncover(newdata,(mfi.x,mfi.y),mfi.player_index)
        elif mfi.button==2:
            self._flag(newdata,(mfi.x,mfi.y),mfi.player_index)
        elif mfi.button==3:
            self._superclick(newdata,(mfi.x,mfi.y),mfi.player_index)

        return MineFieldState(newdata)


    def calculate_scores(self):
        scores={}
        for coords in self:
            cell=self[coords]
            score=cell.score()
            if score is not None:
                if score[0] not in scores:
                    scores[score[0]]=0
                scores[score[0]] += score[1]
        return scores

    def check_all_opened(self, player_filter=(1,2,3,4)):
        all_open=True
        for coords in self:
            if self[coords].owner in player_filter or self[coords].owner == 0:
                if (not self[coords].is_mine) and self[coords].state != CellState.clicked:
                    # We can return early here
                    # But we intentionally don't, since that would mean this process'
                    # running time would get longer as the board gets filled up.
                    # This could make the performance of the server vary wildly,
                    # making debugging & performance analysis harder.
                    # So, to ensure a more constant load, an early return in not used.
                    all_open=False

        return all_open


    @classmethod
    def _superclick(cls,data,center_coords,player_index):
        '''
        Superclick (left+right)
        '''

        valid_coords=[]
        for delta in _neighbor_deltas:
            coords=Tuples.add(center_coords,delta)
            if not data.in_bounds(coords):
                continue
            valid_coords.append(coords)

        minecount = 0
        for coords in valid_coords:
            if data[coords].state==CellState.flagged:
                minecount+=1
            elif data[coords].state==CellState.clicked and data[coords].is_mine:
                minecount+=1

        if minecount==data[center_coords].number:
            for coords in valid_coords:
                cls._uncover(data,coords,player_index)

    @classmethod
    def _flag(cls,data,coords,player_index):
        '''
        Place a flag
        '''
        if data[coords].state == CellState.flagged:
            if data[coords].owner==player_index:
                data[coords] = data[coords].modify(state=CellState.clickable)

        elif data[coords].can_click_by(player_index):
            data[coords]=data[coords].modify(state=CellState.flagged)

    @classmethod
    def _uncover(self,data,initial_coords,player_index):
        '''
        Uncover a cell, expanding outwards if possible.
        '''
        uncover_queue=[]
        uncover_queue.append(initial_coords)

        while uncover_queue:
            coords = uncover_queue.pop(0)
            cell=data[coords]
            if cell.can_click_by(player_index):

                data[coords]=data[coords].modify(state=CellState.clicked,
                                                 owner=player_index)

                if data[coords].is_mine:
                    pass # _could_ do something here

                autoclick= (cell.number==0) and (not cell.is_mine)

                # Modify neighbors
                for delta in _neighbor_deltas:
                    newcoords = Tuples.add(coords, delta)
                    if not data.in_bounds(newcoords):
                        continue

                    if data[newcoords].state == CellState.locked:
                        data[newcoords]=data[newcoords].modify(state=CellState.clickable,
                                                            owner=player_index)

                    if newcoords in uncover_queue:
                        continue  # no duplicates
                    if autoclick:
                        uncover_queue.append(newcoords)

            else:
                pass



class MineFieldEventStack():
    '''
    A MineFieldEventStack consists of two data:
      - Base State, an instance of MineFieldState
      - Deltas, a list of MineFieldInputs
    User inputs can be added to the deltas list, and then can be
    processed in order to produce the final result. > calculate_current_state()

    The game server can ACK deltas to remove them from the queue
    or replace the base state.
    This data structure is a key to maintaing syncronization with the server
    while maintaing responsiveness of the game.
    '''
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self._base_state=None
        self._deltas=list()
        self._current_input_index=4000
    def set_base_state(self,mfs):
        self._base_state=mfs
        #self._deltas=list() #<<<WTF????? WHY WAS THIS HERE IN THE FIRST PLACE????
    def add_input(self,mfi):
        self._current_input_index+=1
        self._deltas.append((self._current_input_index,mfi))
        #print("MineFieldEventStack queue size:",len(self._deltas),"just added input #",self._current_input_index)
        return self._current_input_index
    def ack_until(self,input_index):
        self._deltas=[i for i in self._deltas if i[0]>input_index]

       # print("input ACK until",input_index,"remaining deltas:",len(self._deltas))

    def calaulate_current_state(self):
        if self._base_state is None:
            return None
        state=self._base_state
        for delta in self._deltas:
            mfi=delta[1]
            state=state.process_input(mfi)
        return state



class MineFieldGenerator:
    @classmethod
    def generate_pure_random(cls, x, y, ratio, players):
        '''
        Generate & return a purely random minefield.
        x,y = Field dimensions
        ratio = Probability of a cell having a mine.
        Note that all cells are randomly rolled independently;
        a field with 100 cells and 5% ratio may not have 5 mines - there may be much more (or less)
        '''

        data = multiarray.MultiDimArray(x, y)
        for coords in data:
            data[coords] = (random.random() < ratio)
        return cls.generate_from_minemap(data,players)

    @classmethod
    def generate_symmetrical(cls, x, y, ratio, player):
        '''
        Generate a symmetrical minefield.
        All the mines will be point-symmetrical, the center point being the center of the field.
        Other than that, is mostly same as generate_pure_random function.
        '''

        data = multiarray.MultiDimArray(x, y)

        center_coords = ((x - 1) / 2, (y - 1) / 2)

        for coords in data:
            # Some vector math
            delta = Tuples.sub(coords, center_coords)
            delta_neg = Tuples.neg(delta)
            reflected = Tuples.round(Tuples.add(center_coords, delta_neg))

            if data[reflected] is None:  # not yet generated! generate own.
                data[coords] = (random.random() < ratio)
            else:  # there is data at the other end - copy that
                data[coords] = data[reflected]

        return cls.generate_from_minemap(data,player)

    @classmethod
    def generate_from_minemap(cls, minemap, players=2):
        '''
        Initialize a minefield.
        data is a multiarray.MultiDimArray with boolean values, with dimension x,y.
        A value of True means a mine is present at that coordinates.
        '''

        if players not in (2,4):
            raise Exception("Invalid number of players!")


        # Before doing anything, calculate the adjacent mine numbers
        numbers = multiarray.MultiDimArray(*minemap.dimensions)

        for coords in minemap:
            count = 0
            for delta in _neighbor_deltas:
                deltacoords=Tuples.add(coords, delta)
                if not minemap.in_bounds(deltacoords):
                    continue
                if minemap[deltacoords]:
                    count += 1

            numbers[coords] = count

        # the Cells are also stored in a MultiDimArray, with same dimensions as the source data.
        data = multiarray.MultiDimArray(*minemap.dimensions)

        # Fill in with ImmutableCells
        for coords in minemap:
            newcell = ImmutableCell(
                state=CellState.locked,
                owner=0, # no one owns it
                is_mine=minemap[coords],
                number=numbers[coords]
            )
            data[coords] = newcell

        # Open up edges
        edges_L=((0,i) for i in range(data.y))
        edges_R=((data.x-1,i) for i in range(data.y))
        edges_U = ((i, 0) for i in range(1,data.x))
        edges_D = ((i, data.y-1) for i in range(data.x-1))

        if players==2:
            for coords in edges_L:
                data[coords]=data[coords].modify(
                    owner=1,
                    state=CellState.clickable
                )
            for coords in edges_R:
                data[coords]=data[coords].modify(
                    owner=2,
                    state=CellState.clickable
                )
        if players==4:

            for coords in edges_L:
                data[coords]=data[coords].modify(
                    owner=1,
                    state=CellState.clickable
                )
            for coords in edges_R:
                data[coords]=data[coords].modify(
                    owner=4,
                    state=CellState.clickable
                )
            for coords in edges_U:
                data[coords]=data[coords].modify(
                    owner=2,
                    state=CellState.clickable
                )
            for coords in edges_D:
                data[coords]=data[coords].modify(
                    owner=3,
                    state=CellState.clickable
                )

        return MineFieldState(data)

