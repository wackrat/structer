"""
Space efficient index for binary search
"""

from bisect import bisect
import struct

from . import named

# pylint: disable=undefined-variable,pointless-statement

class Interval(named.Tuple):
    """
    Three integers or integer sequences defining spans and values
    """
    start, step, value

def pack(fmt, *sequence):
    """
    Return a memoryview on a packed Struct for a sequence and format
    Return a range instead if the sequence allows that
    """
    if len(sequence) + sequence[0] == sequence[-1] + 1:
        arange = range(sequence[0], sequence[-1] + 1)
        if type(sequence)(arange) == sequence:
            return arange
    return memoryview(struct.pack(len(sequence)*fmt, *sequence)).cast(fmt)

class Intervals(object):
    """
    Space efficient index for binary search, sorted by start
    The intervals attribute is a named.Tuple with start, step, value attributes
    Each attribute is either a packed sequence or a range
    """
    def __init__(self, iterable, formats="QQQ"):
        self.intervals = Interval(*(pack(*sequence)
                                    for sequence in zip(formats, *sorted(iterable))))

    def __getitem__(self, key):
        index = bisect(self.intervals.start, key) - 1
        if index < 0:
            raise KeyError
        interval = Interval(*(element[index] for element in self.intervals))
        assert key >= interval.start
        if key > interval.start + interval.step:
            raise KeyError
        return interval.value

    def __contains__(self, key):
        try:
            return self[key] is not None
        except KeyError:
            return False
