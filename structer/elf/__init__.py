"""
Extensible Link Format represented by named.Struct subclasses
"""

import re
import struct
from .. import CacheAttr
from ..named import StructArray, VarStructArray
from ..intervals import Intervals
from . import enums, header
from .enums import PType, AUXVType

class Elf(object):
    """
    Extensible Link Format
    """
    def __new__(cls, mem):
        ident = header.Ident(mem)
        kwargs = dict(byteorder=ident.byteorder, wordsize=ident.wordsize)
        # pylint: disable=unexpected-keyword-arg
        head = header.Header(mem, **kwargs)
        elf = super().__new__(cls.elftype(head))
        elf.mem = mem
        elf.kwargs = kwargs
        elf.header = head
        return elf

    def __getattr__(self, name):
        cls = getattr(header, name)(**self.kwargs)
        setattr(self, name, cls)
        return cls

    @classmethod
    def elftype(cls, head):
        """ Choose class from header type field """
        return {enums.Type.Core : Core}.get(head.type, Elf)

    @CacheAttr
    def segs(self):
        """ Sequence of program segment headers """
        head = self.header
        phdr = self.mem[head.phoff:][:head.phnum * head.phentsize]
        return StructArray(phdr, self.Phdr)

    @CacheAttr
    def addrindex(self):
        """Space efficient index for binary search """
        return Intervals((seg.vaddr, seg.filesz, index)
                         for index, seg in enumerate(self.segs)
                         if seg.type == PType.Load)

    def fetch(self, addr, size=0):
        """ memoryview slice at specified address """
        seg = self.segs[self.addrindex[addr]]
        offset = addr - seg.vaddr
        assert offset >= 0
        limit = seg.filesz - offset
        if size == 0 or size > limit:
            size = limit
        if size < 0:
            raise KeyError
        return self.mem[seg.offset + offset:][:size]

    @CacheAttr
    def notetype(self):
        """ Generic ELF note """
        return self.Note

    def notes(self):
        """ elements within segments of type Note """
        for seg in self.segs:
            if seg.type == PType.Note:
                notes = self.mem[seg.offset:][:seg.filesz]
                for note in VarStructArray(notes, self.notetype):
                    yield note

    def note(self, ntype):
        """ First note matching specified type """
        for note in self.notes():
            if note.type == ntype:
                return note

    def build_id(self):
        """ Contents of GNUNote.Build_ID note """
        return self.note(enums.GNUNote.Build_ID).desc

    def find(self, pattern):
        """
        Generator for re search on seg contents
        Does not handle hits which cross seg boundaries
        """
        for seg in self.segs:
            if seg.type == PType.Load:
                for hit in pattern.finditer(self.fetch(seg.vaddr)):
                    yield seg.vaddr + hit.start()

    def findbytes(self, bytes):
        """ Generator to locate specified bytes """
        return self.find(re.compile(re.escape(bytes)))

    def findwords(self, *words, fmt="Q"):
        """ Generator to locate specified word sequence """
        return self.find(re.compile(b''.join(re.escape(struct.pack(fmt, word)) for word in words)))

    @CacheAttr
    def auxv(self):
        """ ELF auxiliary vector, keyed by type """
        auxv = self.note(enums.CoreNote.Auxv)
        if auxv:
            return dict((aux.type, aux.val)
                        for aux in StructArray(auxv.desc, self.Auxv))

class Core(Elf):
    """
    ELF crash dump
    """
    def __new__(cls, mem):
        """ Validate type field """
        elf = super().__new__(cls, mem)
        assert cls.elftype(elf.header) is cls, "Not a core"
        return elf

    def size(self):
        """ File size predicted by header contents """
        last = self.segs[self.addrindex.intervals.value[-1]]
        assert last.type == PType.Load
        return last.offset + last.filesz

    @CacheAttr
    def notetype(self):
        """ ELF Note for Core """
        return self.CoreNote

    @CacheAttr
    def filenote(self):
        """ Note with list of file mappings """
        note = self.note(enums.CoreNote.File)
        if not note:
            return ()
        note = self.FileNote(note.desc)
        return header.FileMappings(note.count, note.Mem, **self.kwargs)

    def build_ids(self):
        """ Iterate over readonly executable filenote Elf headers """
        for mapping in self.filenote:
            if mapping.offset == 0:
                seg = self.segs[self.addrindex[mapping.start]]
                if seg.filesz > 0 and seg.flags == 5:
                    assert mapping.start == seg.vaddr
                    head = self.mem[seg.offset:][:seg.filesz]
                    yield mapping.name, seg.vaddr, Elf(head).build_id()

    def linkmap(self, addr):
        """ Instantiate linkmap at specified address """
        return self.LinkMap(self.fetch(addr))

    @CacheAttr
    def linkmaps(self):
        """ Return chain of loaded objects from dynamic section Debug element """
        auxv = self.auxv
        try:
            segs = StructArray(self.fetch(auxv[AUXVType.Phdr],
                                          auxv[AUXVType.PHEnt] * auxv[AUXVType.PHNum]),
                               self.Phdr)
        except KeyError:
            return ()
        dyn, = (seg for seg in segs if seg.type == PType.Dynamic)
        phdr, = (seg for seg in segs if seg.type == PType.Phdr)
        delta = auxv[AUXVType.Phdr] - phdr.vaddr
        debug, = (element for element in StructArray(self.fetch(dyn.vaddr + delta,
                                                                dyn.filesz), self.Dyn)
                  if element.tag == enums.DTag.Debug)
        return header.LinkMaps(self.fetch, self.linkmap,
                               self.DebugInfo(self.fetch(debug.val)).map)
