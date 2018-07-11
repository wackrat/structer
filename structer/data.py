"""
Data elements for named.Struct with keyword variants
The __struct_format__ attribute is required by named.Struct,
and is calculated on demand from keyword values.
Int and Long use different keywords (length and wordsize).
Int subclasses are independent of elf.enums.WordSize
"""

import re
from datetime import datetime

from . import Meta, ClassAttr

class Data(metaclass=Meta, length=0):
    """
    Base class for generating class variants by keyword
    Keyword values are provided as attributes if otherwise absent.
    """
    @ClassAttr
    def __struct_format__(self):
        return '{}s'.format(self.__namespace__.length)

class Bytes(bytes, Data):
    """
    bytes data element with length keyword, defaulting to zero
    Render in hexadecimal
    """
    def __str__(self):
        return (len(self)*"{:02x}").format(*self)

    def __repr__(self):
        return str(self)

class String(Bytes):
    """
    Bytes subclass for null terminated strings
    """
    pattern = re.compile(b'^[^\0]*')

    def __str__(self):
        return self.pattern.match(self).group().decode()

class Nulls(Bytes):
    """
    bytes data element asserted to be all nulls, returning None
    """
    def __new__(cls, bites):
        assert bites == b'\0'* cls.length

def signer(cls, char):
    """
    Use upper case for unsigned format character
    """
    return char if cls.signed else char.upper()

class Int(int, Data, signed=False, base=None):
    """
    int data element with 1, 2, 4, or 8 bytes, defaulting to 1
    the length keyword value is the base two log of the byte count.
    the base keyword changes the meaning of the length keyword,
    specifying the length of a bytes object sent to the int constructor
    """
    def __new__(cls, value):
        if cls.base is None:
            return super().__new__(cls, value)
        else:
            return super().__new__(cls, value, base=cls.base)

    @ClassAttr
    def __struct_format__(self):
        length = self.length
        if self.base is None:
            return signer(self, "bhiq"[length])
        else:
            return '{}s'.format(length)

    def __len__(self):
        length = self.length
        if self.base is None:
            return 1 << length
        else:
            return length

class Long(Int, wordsize=0):
    """
    int data element with 32 or 64 bits, defaulting to native
    The wordsize keyword numbering matches elf.enums.WordSize
    """
    @ClassAttr
    def __struct_format__(self):
        return signer(self, "niq"[self.__namespace__.wordsize])

class PString(Int):
    """
    String with prefix length
    """
    def __call__(self, mem, offset):
        return String(mem[offset:][:self])

class Payload(Int(length=2)):
    """
    memoryview slice of specified size, defaulting to 32 bit
    """
    def __init__(self, size):
        super().__init__()
        self.size = size
    def __call__(self, mem, offset):
        return mem[offset:][:self.size]

def pad(offset, align):
    """
    Number of bytes to add to offset to align it
    """
    return (align - (offset % align)) % align

class Pad(Bytes, align=1):
    """
    slice of nulls to round the offset to the specfied alignment
    """
    def __call__(self, mem, offset):
        padding = mem[offset:][:pad(offset, self.align)]
        assert padding == len(padding) * b'\0'
        return padding

class Strings(Bytes):
    """
    Contiguous range of null terminated strings
    """
    class Iter(object):
        """
        Iterate over null terminated strings
        """
        pattern = re.compile(b'([^\0]*)\0')

        def __init__(self, mem, offset, count):
            self.mem = mem[offset:]
            self.count = count

        def __iter__(self):
            count = self.count
            for match in self.pattern.finditer(self.mem):
                yield match.group(1).decode()
                if count:
                    count -= 1
                    if not count:
                        break

        def __len__(self):
            return len(self.mem)

    def __call__(self, mem, offset, count=0):
        return self.Iter(mem, offset, count)

class MTime(Int):
    """
    Return datetime decoded from Int
    """
    def __new__(cls, value):
        return datetime.utcfromtimestamp(int(super().__new__(cls, value)))

class Tail(Bytes):
    """
    The remaining space in this slice
    """
    def __call__(self, mem, offset):
        return mem[offset:]
