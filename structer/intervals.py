"""
Space efficient index for binary search
"""

from bisect import bisect
import struct

from . import named, CacheAttr

class Seg(named.Tuple):
    """
    Address, and offset range
    """
    addr, start, length

def combine(segs):
    """ Combine adjacent segs which have no intervening gaps """
    segs = sorted(segs)
    for index in range(len(segs), 1, -1):
        low, high = segs[index-2:index]
        if high.addr - low.addr == low.length and low.start + low.length == high.start:
            segs[index-2:index] = [Seg(low.addr, low.start, low.length + high.length)]
    return segs

class Intervals(object):
    """
    Space efficient index for binary search, sorted by address
    The segs attribute has multiple (packed) values rather than individual values.
    """
    def __init__(self, segs, fmt="Q"):
        segs = combine(segs)
        fmts = fmt * len(segs)
        self.segs = Seg(*(memoryview(struct.pack(fmts, *seg)).cast(fmt)
                          for seg in zip(*sorted(segs))))

    def seg(self, index):
        """ Return Seg at specified index, from packed values """
        return Seg(*(element[index] for element in self.segs))

    @CacheAttr
    def end(self):
        """
        Offset just beyond the last element
        Do not assume offsets are sorted; the address is the sort key.
        """
        return max(seg.start + seg.length for seg in self)

    def __getitem__(self, key):
        index = bisect(self.segs.addr, key) - 1
        if index < 0:
            raise KeyError
        seg = self.seg(index)
        delta = key - seg.addr
        assert delta >= 0
        if delta > seg.length:
            raise KeyError
        return Seg(key, seg.start + delta, seg.length - delta)

    def __contains__(self, key):
        try:
            return self[key] is not None
        except KeyError:
            return False

    def __iter__(self):
        for index in range(len(self.segs.addr)):
            yield self.seg(index)
