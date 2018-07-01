"""
Data elements for named.Struct with keyword variants
The __struct_format__ attribute is required by named.Struct,
and is calculated on demand from keyword values.
Int and Long use different keywords (length and wordsize).
Int subclasses are independent of elf.enums.WordSize
"""

import re

from . import Meta, ClassAttr

class Data(metaclass=Meta, length=0):
    """
    Base class for generating class variants by keyword
    """
    @ClassAttr
    def __struct_format__(self):
        return '{}s'.format(self.__namespace__.length)

    def __getattr__(self, name):
        return self.__namespace__.__getattr__(name)

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

def signer(cls, char):
    """
    Use upper case for unsigned format character
    """
    return char if cls.__namespace__.signed else char.upper()

class Int(int, Data, signed=False):
    """
    int data element with 1, 2, 4, or 8 bytes, defaulting to 1
    the length keyword value is the base two log of the byte count
    """
    @ClassAttr
    def __struct_format__(self):
        return signer(self, "bhiq"[self.__namespace__.length])

class Long(Int, wordsize=0):
    """
    int data element with 32 or 64 bits, defaulting to native
    The wordsize keyword numbering matches elf.enums.WordSize
    """
    @ClassAttr
    def __struct_format__(self):
        return signer(self, "niq"[self.__namespace__.wordsize])

class Strings(Bytes):
    """
    Contiguous range of null terminated strings
    """
    class Iter(object):
        """
        Iterate over null terminated strings
        """
        pattern = re.compile(b'([^\0]*)\0')

        def __init__(self, mem, offset):
            self.mem = mem[offset:]

        def __iter__(self):
            for match in self.pattern.finditer(self.mem):
                yield match.group(1).decode()

        def __len__(self):
            return len(self.mem)

    def __call__(self, mem, offset):
        return self.Iter(mem, offset)

class Tail(Bytes):
    """
    The remaining space in this slice
    """
    def __call__(self, mem, offset):
        return mem[offset:]
