"""
ELF file header
"""

from .. import CacheAttr, data
from ..named import Struct, VarStruct, StructArray, Tuple
from ..data import Long
from . import enums, notes
from .dtags import DTag

Int1, Int2, Int3 = (data.Int(length=length) for length in (1, 2, 3))

class Ident(Struct):
    """
    The first 16 bytes of an ELF file
    """
    magic = enums.Magic
    wordsize = enums.WordSize
    byteorder = enums.ByteOrder
    version = enums.Version
    osabi = enums.OSABI
    abiversion = data.Int
    padding = data.Nulls(length=7)

    @CacheAttr
    def kwargs(self):
        """ wordsize and byteorder """
        return dict(byteorder=self.byteorder, wordsize=self.wordsize)

class Header(Ident):
    """
    Header of an ELF file
    """
    type = enums.Type
    machine = enums.Machine
    Version = enums.Version(length=2)
    entry, phoff, shoff = 3*(Long,)
    flags = Int2
    ehsize, phentsize, phnum = 3*(Int1,)
    shentsize, shnum, shstrndx = 3*(Int1,)

    def __new__(cls, mem, offset=0):
        return super().__new__(cls(**Ident(mem).kwargs), mem, offset)

class Phdr(object):
    """
    ELF program segment header
    """
    class Phdr32(Struct):
        """ 32 bit program segment header """
        type = enums.PType
        offset, vaddr, paddr, filesz, memsz, flags, align = 7*(Int2,)

    class Phdr64(Struct):
        """ 64 bit program segment header """
        type = enums.PType
        flags = Int2
        offset, vaddr, paddr, filesz, memsz, align = 6*(Int3,)

    def __new__(cls, **kwargs):
        """ Choose the class indexed by the wordsize """
        return (None, cls.Phdr32, cls.Phdr64)[kwargs['wordsize']](**kwargs)

class Shdr(Struct):
    """
    ELF section header
    """
    name = Int2
    type = enums.SType
    flags, addr, offset, filesz = 4*(Long,)
    link, info, = 2*(Int2,)
    align, entsize = 2*(Long, )

class Note(VarStruct):
    """
    Elf Note
    """
    name = data.PString(length=2)
    namepad = data.Pad(align=4)
    payload = data.Payload
    paypad = data.Pad(align=4)
    notetype = Int2
    def __call__(self):
        return getattr(notes, str(self.name))(self.notetype), self.payload

class Span(Struct):
    """
    Address range and offset
    """
    start, end, offset = 3*(Long,)

class FileMapping(Tuple):
    """ One element of a FileNote """
    name, start, end, offset

class FileNote(VarStruct):
    """
    Note containing file mappings in ELF core
    """
    count, align, tail = Long, Long, data.Tail

    @CacheAttr
    def spans(self):
        """ Sequence of spans """
        span = Span(byteorder=self.byteorder, wordsize=self.count.wordsize)
        return StructArray(self.tail[:self.count*len(span)], span)

    @CacheAttr
    def names(self):
        """ Null terminated strings """
        return data.Strings(0)(self.tail, len(self.spans.mem), len(self.spans))

    def __iter__(self):
        for name, span in zip(self.names, self.spans):
            yield FileMapping(name, *span)

class Auxv(Struct):
    """
    ELF auxiliary vector
    """
    type = enums.AUXVType
    val = Long

class Dyn(Struct, tag=DTag):
    """ ELF dynamic section """
    tag = DTag
    val = Long

class DebugInfo(Struct):
    """ Shared object loading """
    version = Long
    map = Long
    brk = Long
    state = enums.DebugState
    ldbase = Long

class LinkMap(VarStruct, fetch=None):
    """ Dynamically loaded object """
    addr = Long
    class name(Long, fetch=None):
        """ Address of null terminated string """
        def __call__(self, mem, offset):
            try:
                return str(data.String(self.fetch(self)))
            except KeyError:
                return ''
    dyn, next, prev = 3*(Long,)
    def __iter__(self):
        while self.next:
            self = type(self)(self.fetch(self.next))
            if self.name:
                yield self
