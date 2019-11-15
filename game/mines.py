import enum
from util.utils import Tuples
import util.utils
import random
from util import multiarray
import collections

_neighbor_deltas = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))

class CellState(enum.Enum):
    '''
    Enum of possible cell states
    '''
    locked = enum.auto()
    clickable=enum.auto()
    clicked = enum.auto()
    flagged = enum.auto()


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


    def __eq__(self, other):
        return ((self._state == other._state) and
                (self._owner == other._owner) and
                (self._is_mine == other._is_mine) and
                (self._number == other._number))

    def __ne__(self,other):
        return not self.__eq__(other)


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


# Stores user input for "playback"
MineFieldInput=collections.namedtuple("MineFieldInput",("x","y","button","player_index"))

class MineFieldState:
    '''
    An IMMUTABLE minefield; a 2d grid of ImmutableCells.
    There are two main ways of initializing a MineFieldState:
      - Converting from MineField
      - Applying MineFieldInputs to existing MineFieldState
    '''

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
                    print("KABOOM on",coords)
                    # TODO handle mine-clicks
                autoclick=(cell.number==0)

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
    def set_base_state(self,mfs):
        self._base_state=mfs
        self._deltas=list()
    def add_input(self,mfi):
        self._deltas.append(mfi)
        print("MineFieldEventStack queue size:",len(self._deltas))
    def ack_until(self):
        # TODO this
        pass
    def calaulate_current_state(self):
        if self._base_state is None:
            return None
        state=self._base_state
        for mfi in self._deltas:
            state=state.process_input(mfi)
        return state

class MineManager(util.utils.CallbackEnabledClass):
    '''
    Actually handles user input and dispatches server communication requests
    '''
    def __init__(self, player_index, *args, **kwargs):
        super().__init__(*args,**kwargs)
        self._state_cache=None
        self._event_stack=MineFieldEventStack()

        self._player_index=player_index

    def debug_change_pidx(self,n):
        self._player_index=n
    def _invalidate_cache(self):
        self._state_cache=None

    def _recalculate_cache(self):
        self._state_cache=self._event_stack.calaulate_current_state()
    def user_input(self,coords,button):

        self._event_stack.add_input(
            MineFieldInput(x=coords[0],
                           y=coords[1],
                           button=button,
                           player_index=self._player_index))

        self._invalidate_cache()
        self._call_update_callbacks()
    def server_sync(self,newstate):
        self._event_stack.set_base_state(newstate)
        self._invalidate_cache()
        self._call_update_callbacks()
    def get_state(self):
        if self._state_cache is None:
            self._recalculate_cache()
        return self._state_cache

class MineFieldGenerator:
    @classmethod
    def generate_pure_random(cls, x, y, ratio):
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
        return cls.generate_from_minemap(data)

    @classmethod
    def generate_symmetrical(cls, x, y, ratio):
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

        return cls.generate_from_minemap(data)

    @classmethod
    def generate_from_minemap(cls, minemap):
        '''
        Initialize a minefield.
        data is a multiarray.MultiDimArray with boolean values, with dimension x,y.
        A value of True means a mine is present at that coordinates.
        '''


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
                owner=None,
                is_mine=minemap[coords],
                number=numbers[coords]
            )
            data[coords] = newcell

        # Open up edges
        for i in range(data.y):
            data[0,i]=data[0,i].modify(
                owner=1,
                state=CellState.clickable
            )
            data[data.x-1, i] = data[data.x-1, i].modify(
                owner=2,
                state=CellState.clickable
            )

        return MineFieldState(data)

