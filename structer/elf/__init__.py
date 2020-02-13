"""
Extensible Link Format represented by named.Struct subclasses
"""

import re
import struct
from .. import CacheAttr, MultiDict, AttrDict, LazyDict
from ..named import StructArray, VarStructArray
from ..intervals import Seg, Intervals
from ..data import Bytes
from . import header
from .enums import PType, SType, Type
from . import dtags
from .notes import GNU, CORE

class ElfError(Exception):
    """ Handle header unpack exceptions """

def elftype(head):
    """ Choose class from header type field """
    return {Type.Core : Core}.get(head.type, Elf)

def segdict(mem, segtype):
    """ Group segments and sections by type """
    return AttrDict((seg.type, seg) for seg in StructArray(mem, segtype))

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
        elf.kwargs = {**head.kwargs, **dict(fetch=elf.fetch)}
        return elf

    def __getattr__(self, name):
        cls = getattr(header, name)(**self.kwargs)
        setattr(self, name, cls)
        return cls

    @CacheAttr
    def segs(self):
        """ Sequence of program segment headers """
        head = self.header
        return segdict(self.mem[head.phoff:][:head.phnum * head.phentsize], self.Phdr)

    @CacheAttr
    def loadsegs(self):
        """ program segment headers of type Load, keyed by address """
        return LazyDict((seg.vaddr, seg) for seg in self.segs[PType.Load])

    @CacheAttr
    def sects(self):
        """ Sequence of section headers """
        head = self.header
        return segdict(self.mem[head.shoff:][:head.shnum * head.shentsize], self.Shdr)

    @CacheAttr
    def addrindex(self):
        """Space efficient index for binary search """
        return Intervals(Seg(seg.vaddr, seg.offset, seg.filesz)
                         for seg in self.segs[PType.Load])

    def fetch(self, addr, size=0):
        """ memoryview slice at specified address """
        seg = self.addrindex[addr]
        offset = addr - seg.addr
        length = seg.length - offset
        if size == 0 or size > length:
            size = length
        assert size >= 0
        offset += seg.start
        if offset + size > len(self.mem):
            assert offset + size <= self.addrindex.end
            raise ElfError("truncated file")
        return self.mem[offset:][:size]

    def notes(self, segs):
        """ elements within segments of type Note """
        for seg in segs:
            for note in VarStructArray(self.mem[seg.offset:][:seg.filesz], self.Note):
                yield note()

    @CacheAttr
    def note(self):
        """
        Notes keyed by type
        Prefer notes from section headers, if present.
        """
        notes = MultiDict(self.notes(self.sects[SType.Note]))
        return notes if notes else MultiDict(self.notes(self.segs[PType.Note]))

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

    @CacheAttr
    def dtag(self):
        """ Enum for dynamic tag values """
        return getattr(dtags, str(self.header.machine), dtags.DTag)(**self.kwargs)

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
        segs = segdict(mem, self.Phdr)
        phdr, dyn = segs.Phdr, segs.Dynamic
        delta = auxv.Phdr - phdr.vaddr
        dyns = AttrDict(StructArray(self.fetch(dyn.vaddr + delta, dyn.filesz),
                                    self.Dyn(tag=self.dtag)))
        linkmap = self.LinkMap(self.fetch(self.DebugInfo(self.fetch(dyns.Debug)).map))
        assert linkmap.addr + dyn.vaddr == linkmap.dyn
        return linkmap
