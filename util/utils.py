
import math
import json


def object_to_json_bytes(obj):
    return json.dumps(obj).encode("utf-8")
def json_bytes_to_object(b):
    return json.loads(b.decode("utf-8"))
def restore_int_keys(d):
    res=dict()
    for orig_key in d:
        value=d[orig_key]
        if isinstance(value,dict):
            value=restore_int_keys(value)
        try:
            new_key=int(orig_key)
        except ValueError:
            new_key=orig_key
        res[new_key]=value
    return res

class Tuples:
    '''
    Helper class for simple vector computations on tuples.
    Note that all functions work with tuples of all sizes.
    (But for functions that take 2 tuples, the sizes must match)
    '''

    @classmethod
    def forelem(cls, a, f):
        # Run a function on each element
        return tuple((f(i) for i in a))

    @classmethod
    def forelem2(cls, a, b, f):
        # Run a function on each element, on two tuples.
        if len(a) != len(b):
            raise Exception("Mismatched tuple length")
        return tuple((f(a[i], b[i]) for i in range(len(a))))

    @classmethod
    def add(cls, a, b):
        return cls.forelem2(a, b, lambda x, y: x + y)

    @classmethod
    def neg(cls, a):
        return cls.forelem(a, lambda x: -x)

    @classmethod
    def sub(cls, a, b):
        return cls.add(a, cls.neg(b))

    @classmethod
    def mult(cls, a, n):
        return cls.forelem(a, lambda x: x * n)

    @classmethod
    def element_wise_mult(cls,a,b):
        return cls.forelem2(a,b,lambda x,y:x*y)

    @classmethod
    def element_wise_div(cls, a, b):
        return cls.forelem2(a, b, lambda x, y: x / y)

    @classmethod
    def div(cls, a, n):
        return cls.mult(a, 1 / n)

    @classmethod
    def round(cls, a):
        return cls.forelem(a, lambda x: round(x))

    @classmethod
    def floor(cls,a):
        return cls.forelem(a,lambda x:math.floor(x))



class CallbackEnabledClass():
    '''
    Superclass for any classes wanting to add a callback listener
    '''
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)

        self._callbacks=list()
        self._callback_paused=False

    def add_update_callback(self,cb):
        self._callbacks.append(cb)

    def remove_update_callback(self,cb):
        self._callbacks.remove(cb)

    def _call_update_callbacks(self,data=None):
        if self._callback_paused:
            return
        for i in self._callbacks:
            i(data)

    def _pause_callbacks(self):
        self._callback_paused=True
    def _unpause_callbacks(self):
        self._callback_paused=False

def perline_prefix(s,p):
    return "\n".join([(p+i) for i in s.split("\n")])

def extract_bit(byte, index):
    return (byte & (1 << index)) != 0