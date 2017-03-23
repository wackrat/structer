"""
ELF file header
"""

from ..named import Struct, VarStruct, StructArray, Tuple
from ..data import Bytes, Int, Long, Strings
from . import enums

class Ident(Struct):
    """
    The first 16 bytes of an ELF file
    """
    magic = enums.Magic
    wordsize = enums.WordSize
    byteorder = enums.ByteOrder
    version = enums.Version
    osabi = enums.OSABI
    abiversion = Int
    padding = Bytes(length=7)

class Header(Struct):
    """
    Header of an ELF file
    """
    ident = Ident
    type = enums.Type
    machine = enums.Machine
    version = enums.Version(length=2)
    entry, phoff, shoff = 3*(Long,)
    flags = Int(length=2)
    ehsize, phentsize, phnum = 3*(Int(length=1),)
    shentsize, shnum, shstrndx = 3*(Int(length=1),)

class Phdr(object):
    """
    ELF program segment header
    """
    class Phdr32(Struct):
        """ 32 bit program segment header """
        type = enums.PType
        offset, vaddr, paddr, filesz, memsz, flags, align = 7*(Int(length=2),)

    class Phdr64(Struct):
        """ 64 bit program segment header """
        type = enums.PType
        flags = Int(length=2)
        offset, vaddr, paddr, filesz, memsz, align = 6*(Int(length=3),)

    def __new__(cls, **kwargs):
        """ Choose the class indexed by the wordsize """
        return (None, cls.Phdr32, cls.Phdr64)[kwargs['wordsize']](**kwargs)

class PaddedBytes(Int(length=2)):
    """
    byte range of specified length, aligned to 32 bit boundary
    """
    def __init__(self, size):
        super().__init__()
        self.size = (size + 3) & ~3

    def __call__(self, mem, offset):
        return mem[offset:][:self.size]

class NoteName(PaddedBytes):
    """
    name of a note, stored as PaddedBytes
    """
    def __call__(self, mem, offset):
        return enums.NoteName(super().__call__(mem, offset))

class CoreNote(VarStruct):
    """
    Core Note section
    """
    name = NoteName
    desc = PaddedBytes
    type = enums.CoreNote

class Note(VarStruct):
    """
    Elf Note section
    """
    name = NoteName
    desc = PaddedBytes
    type = enums.GNUNote

class Span(Struct):
    """
    Address range and offset
    """
    start, end, offset = 3*(Long,)

# pylint: disable=undefined-variable,pointless-statement

class FileMapping(Tuple):
    """ One element of a FileNote """
    name, start, end, offset

class FileNote(VarStruct):
    """
    Note containing file mappings in ELF core
    """
    count, align = Long, Long

    class Mem(Bytes):
        """ The remaining space in this note """
        def __call__(self, mem, offset):
            return mem[offset:]

class FileMappings(object):
    """
    Iterable representing a FileNote
    """
    def __init__(self, count, mem, **kwargs):
        span = Span(**kwargs)
        length = count * len(span)
        self.spans = StructArray(mem[:length], span)
        self.names = Strings(0)(mem, length)

    def __iter__(self):
        name = iter(self.names)
        for span in self.spans:
            yield FileMapping(next(name), *span)

class Auxv(Struct):
    """
    ELF auxiliary vector
    """
    type = enums.AUXVType
    val = Long

class Dyn(Struct):
    """ ELF dynamic section """
    tag = enums.DTag
    val = Long

class DebugInfo(Struct):
    """ Shared object loading """
    version = Long
    map = Long
    brk = Long
    state = enums.DebugState
    ldbase = Long

class LinkMap(Struct):
    """ Dynamically loaded object """
    addr, name, dyn, next, prev = 5*(Long,)

class LinkMaps(object):
    """ Iterator for chain of LinkMap elements """
    def __init__(self, fetch, linkmap, addr):
        self.fetch = fetch
        self.linkmap = linkmap
        self.addr = addr

    def name(self, linkmap):
        """ Fetch null terminated string from specified LinkMap """
        return Strings.Iter.pattern.match(self.fetch(linkmap.name)).group(1).decode()

    def __iter__(self):
        first = self.linkmap(self.addr)
        assert first.prev == 0
        addr, prev = first.next, self.addr
        while addr:
            linkmap = self.linkmap(addr)
            assert prev == linkmap.prev
            prev, addr = addr, linkmap.next
            if linkmap.name != first.name:
                name = self.name(linkmap)
                if name:
                    new = (linkmap.addr, name, linkmap.dyn, linkmap.next, linkmap.prev)
                    yield tuple.__new__(type(linkmap), new)
