"""
Extensible Link Format represented by named.Struct subclasses
"""

import re
import struct
from .. import CacheAttr, MultiDict, AttrDict
from ..named import StructArray, VarStructArray
from ..intervals import Seg, Intervals
from ..data import Bytes
from . import header
from .enums import PType, AUXVType, Type, DTag
from .notes import GNU, CORE

class ElfError(Exception):
    """ Handle header unpack exceptions """

def elftype(head):
    """ Choose class from header type field """
    return {Type.Core : Core}.get(head.type, Elf)

class Elf(object):
    """
    Extensible Link Format
    """
    def __new__(cls, mem, name=None):
        try:
            head = header.Header(mem)
        except (struct.error, ValueError) as exc:
            raise ElfError(exc)
        elf = super().__new__(elftype(head))
        elf.mem, elf.name, elf.header = mem, name, head
        elf.kwargs = {**head.ident.kwargs, **dict(fetch=elf.fetch)}
        return elf

    def __getattr__(self, name):
        cls = getattr(header, name)(**self.kwargs)
        setattr(self, name, cls)
        return cls

    @CacheAttr
    def segs(self):
        """ Sequence of program segment headers """
        head = self.header
        phdr = self.mem[head.phoff:][:head.phnum * head.phentsize]
        return StructArray(phdr, self.Phdr)

    @CacheAttr
    def loadsegs(self):
        """ program segment headers of type Load, keyed by address """
        return dict((seg.vaddr, seg) for seg in self.segs if seg.type == PType.Load)

    @CacheAttr
    def sects(self):
        """ Sequence of section headers """
        head = self.header
        shdr = self.mem[head.shoff:][:head.shnum * head.shentsize]
        return StructArray(shdr, self.Shdr)

    @CacheAttr
    def addrindex(self):
        """Space efficient index for binary search """
        return Intervals(Seg(seg.vaddr, seg.offset, seg.filesz)
                         for seg in self.segs if seg.type == PType.Load)

    def fetch(self, addr, size=0):
        """ memoryview slice at specified address """
        seg = self.addrindex[addr]
        length = seg.length
        if size == 0 or size > length:
            size = length
        assert size >= 0
        return self.mem[seg.start:][:size]

    def notes(self, segs):
        """ elements within segments of type Note """
        for seg in segs:
            if seg.type == seg.type.Note:
                notes = self.mem[seg.offset:][:seg.filesz]
                for note in VarStructArray(notes, self.Note):
                    yield note()

    @CacheAttr
    def note(self):
        """
        Notes keyed by type
        Work around malformatted Elf objects.
        """
        try:
            return MultiDict(self.notes(self.segs))
        except AttributeError:
            return MultiDict(self.notes(self.sects))

    def build_id(self):
        """ Contents of GNUNote.Build_ID note """
        mem, = self.note[GNU.Build_ID]
        return Bytes(mem)

    def find(self, pattern):
        """ Generator for re search on seg contents """
        for seg in self.addrindex:
            for hit in pattern.finditer(self.mem[seg.start:][:seg.length]):
                yield seg.addr + hit.start()

    def findbytes(self, bites):
        """ Generator to locate specified bytes """
        return self.find(re.compile(re.escape(bites)))

    def findwords(self, *words, fmt="Q"):
        """ Generator to locate specified word sequence """
        return self.find(re.compile(b''.join(re.escape(struct.pack(fmt, word)) for word in words)))

class Core(Elf):
    """
    ELF crash dump
    """
    def __new__(cls, mem, name=None):
        """ Validate type field """
        elf = super().__new__(cls, mem, name)
        assert elftype(elf.header) is cls, "Not a core"
        return elf

    def size(self):
        """ File size predicted by header contents """
        return self.addrindex.end

    @CacheAttr
    def filenote(self):
        """ Note with list of file mappings """
        note, = self.note[CORE.File]
        return self.FileNote(note)

    @CacheAttr
    def auxv(self):
        """ ELF auxiliary vector, keyed by type """
        auxv, = self.note[CORE.Auxv]
        return AttrDict(StructArray(auxv, self.Auxv))

    def elves(self):
        """ Iterate over readonly executable filenote Elf headers """
        for mapping in self.filenote:
            if mapping.offset == 0:
                seg = self.loadsegs[mapping.start]
                if seg.filesz > 0 and seg.flags == 5:
                    head = self.mem[seg.offset:][:seg.filesz]
                    yield seg.vaddr, Elf(head, mapping.name)

    @CacheAttr
    def linkmap(self):
        """ Return chain of loaded objects from dynamic section Debug element """
        auxv = self.auxv
        mem = self.fetch(auxv.Phdr, auxv.PHEnt * auxv.PHNum)
        segs = MultiDict((seg.type, seg) for seg in StructArray(mem, self.Phdr))
        phdr, = segs[PType.Phdr]
        delta = auxv.Phdr - phdr.vaddr
        dyn, = segs[PType.Dynamic]
        dyns = MultiDict(StructArray(self.fetch(dyn.vaddr + delta, dyn.filesz), self.Dyn))
        debug, = dyns[DTag.Debug]
        linkmap = self.LinkMap(self.fetch(self.DebugInfo(self.fetch(debug)).map))
        assert linkmap.addr + dyn.vaddr == linkmap.dyn
        return linkmap
