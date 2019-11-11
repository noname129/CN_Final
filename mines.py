import enum
from tuples import Tuples
import random
import multiarray


class CellState(enum.Enum):
    '''
    Enum of possible cell states
    '''
    hidden = enum.auto()
    uncovered = enum.auto()
    flagged = enum.auto()


class Cell:
    '''
    Class representing a single cell
    '''
    def __init__(self):
        self.state = CellState.hidden  # hidden, uncovered, flagged
        self.priority = None  # Player entity that has the priority over this cell. Not yet used.
        self.is_mine = False  # is this a mine?
        self.number = -1  # Number of adjacent mines


_neighbor_deltas = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))


class MineField:
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
        return MineField(data)

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

        return MineField(data)

    def __init__(self, data):
        '''
        Initialize a minefield.
        data is a multiarray.MultiDimArray with boolean values, with dimension x,y.
        A value of True means a mine is present at that coordinates.
        '''

        # the Cells are also stored in a MultiDimArray, with same dimensions as the source data.
        self._data = multiarray.MultiDimArray(*data.dimensions)

        self._change_listeners = list()

        for coords in data:
            newcell = Cell()
            if data[coords]:  # a mine is present
                newcell.is_mine = True
            self._data[coords] = newcell

        self._populate_numbers()

    def add_change_listener(self, func):
        '''
        Add an event listener that will be notified whenever a cell changes.
        The supplied function will take a single argument, a 2D tuple of the coordinates of the updated cell.
        The aforementioned argument may be None; in that case the entire minefield must be updated.
        '''
        self._change_listeners.append(func)

    def remove_change_listener(self, func):
        self._change_listeners.remove(func)

    def _call_change_listeners(self, coords):
        for i in self._change_listeners:
            i(coords)

    def _populate_numbers(self):
        # calculate surrounding number of mines
        for coords in self:
            count = 0
            for delta in _neighbor_deltas:
                try:
                    if self[Tuples.add(coords, delta)].is_mine:
                        count += 1
                except multiarray.InvalidCoordinatesException:
                    pass
            self[coords].number = count

            if self[coords].is_mine:
                self[coords].number = "X"

        self._call_change_listeners(None)

    def __getitem__(self, coords):
        return self._data[coords]

    def __iter__(self):
        return self._data.__iter__()

    @property
    def x(self):
        '''
        X dimensions.
        '''
        return self._data.x

    @property
    def y(self):
        '''
        Y dimensions.
        '''
        return self._data.y

    def _uncover(self, coords):
        # Uncover a cell
        self._data[coords].state = CellState.uncovered
        self._call_change_listeners(coords)
        if self._data[coords].number == 0:
            # Auto-Expand
            for delta in _neighbor_deltas:
                newcoords = Tuples.add(coords, delta)
                try:
                    if self._data[newcoords].state == CellState.hidden:
                        self._uncover(newcoords)
                except multiarray.InvalidCoordinatesException:
                    pass

    def click(self, coords, button):
        '''
        Click a cell in location specified by coords.
        button needs to be 1, 2, or 3.
        1 = Left click, uncovers a cell.
        2 = Right click, flags a cell.
        3 = L+R click, uncovers all adjacent cells if possible
        '''
        print("click", button, coords)
        if button == 1:
            self._uncover(coords)


        elif button == 2:
            self._data[coords].state = CellState.flagged
            self._call_change_listeners(coords)

        # TODO button 3 logic
