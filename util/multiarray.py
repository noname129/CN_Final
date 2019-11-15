import itertools


def _multiply_all_elements(l):
    res = 1
    for i in l:
        res = res * i
    return res


class InvalidCoordinatesException(Exception):
    pass


class MultiDimArray:
    '''
    Multi Dimensional Array
    A rectangular array of fixed size in any dimensions.
    example: a 4D array of dimension 2x5x3x2
        >> mda = MultiDimArray(2,5,3,2,fill=0)
        >> mda[0,0,0,0]
        0
        >> mda[3,1,1,1]
        InvalidCoordinatesException
        >> mda[0,1,2,1]=5
        >> for coordinates in mda:
            print(coordinates)
        (0,0,0,0)
        (0,0,0,1)
        (0,0,1,0)
        (0,0,1,1)
        (0,0,2,0)
        ...
    '''

    def __init__(self, *dimensions, fill=None, data=None, copytarget=None):
        if copytarget is not None:
            # Copy constructor
            self._dimensions=copytarget._dimensions
            self._num_elements=copytarget._num_elements
            self._data=list(copytarget._data)

        else:
            if not dimensions:  # empty
                dimensions = [0]  # 1D array with 0 size - basically an empty array.

            self._dimensions = tuple(dimensions) # dimension will never change, so change to tuple.

            self._num_elements = _multiply_all_elements(dimensions)

            if data is not None:
                if len(data) != self._num_elements:
                    raise ValueError("Number of data does not match the dimensions!")
                else:
                    self._data = data
            else:
                self._data = [fill] * self._num_elements

    def shallow_copy(self):
        return MultiDimArray(copytarget=self)

    def in_bounds(self,coords):
        if len(coords) != len(self._dimensions):
            raise InvalidCoordinatesException("mismatch")
        for i in range(len(coords)):
            if coords[i] < 0 or coords[i] >= self._dimensions[i]:
                return False
        return True

    def _coord_to_index(self, coords):
        # Coordinates to index
        # A bit computationally-intensive, considering this will be called on every access to the array
        # Maybe optimize it later on

        coord_dim = len(coords)
        data_dim = len(self._dimensions)

        if coord_dim != data_dim:
            raise InvalidCoordinatesException(
                "Received coordinates of dimension {} in a {}-dimensional array! coords: {}".format(coord_dim, data_dim,
                                                                                                    coords))

        for i in range(coord_dim):
            if coords[i] < 0 or coords[i] >= self._dimensions[i]:
                raise InvalidCoordinatesException(
                    "Received {} as the coordinate in the {} place - must be in [0..{}] range!".format(coords[i], i,
                                                                                                       self._dimensions[
                                                                                                           i] - 1))

        final_index = 0
        for i in range(coord_dim):
            index = coords[i]
            for j in range(i + 1, coord_dim):
                index *= self._dimensions[j]

            final_index += index

        return final_index

    @property
    def dimensions(self):
        return self._dimensions

    @property
    def x(self):
        return self._dimensions[0]

    @property
    def y(self):
        return self._dimensions[1]

    @property
    def z(self):
        return self._dimensions[2]

    def __getitem__(self, item):
        return self._data[self._coord_to_index(item)]

    def __setitem__(self, key, value):
        self._data[self._coord_to_index(key)] = value

    def __iter__(self):
        return self.indices()

    def indices(self):
        '''
        All indices - uses itertools
        '''
        return itertools.product(*[range(i) for i in self._dimensions])


def main():
    # Test code
    mda = MultiDimArray(2, 5, 3, 4, fill=0)
    for i in mda:
        print(i)

    mda = MultiDimArray(3, 3, 3, data=[i + 1 for i in range(27)])
    for x in range(3):
        for y in range(3):
            for z in range(3):
                print(mda[x, y, z])


if __name__ == "__main__":
    main()
