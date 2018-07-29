"""
RPM package format represented by named.Struct subclasses
"""

import lzma
import gzip
from .. import LazyDict, CacheAttr, cpio
from ..data import Int, Bytes, String, Strings, Nulls, Payload, Pad, Tail
from ..named import Struct, VarStruct, VarStructs, StructArray
from ..enum import Enum
from ..elf import Elf, ElfError
from .enums import Type, OSnum, Sig, Tag, HeaderTag, TagType

class Lead(Struct):
    """ RPM lead layout """
    class magic(Enum, Bytes, length=4):
        """ Magic number for RPM lead """
        magic = b'\xed\xab\xee\xdb'
    major, minor = 2*(Int,)
    type = Type
    arch = Int(length=1)
    name = String(length=66)
    osnum, sig = OSnum, Sig
    pad = Nulls(length=16)

class Entry(Struct, tag=Tag):
    """
    Header index entry layout
    tag element can be changed with keyword argument
    """
    tag = Tag
    tagtype = TagType
    offset, count = 2*(Int(length=2),)

class Entries(Payload):
    """ Payload scaled by Entry size """
    def __init__(self, size):
        super().__init__(size)
        self.size = size * len(Entry)

class Header(VarStruct, tag=Tag):
    """
    RPM signature and header layout
    tag names provide additional attributes
    """
    class magic(Enum, Bytes, length=3):
        """ Magic number for RPM header """
        magic = b'\x8e\xad\xe8'
    class version(Enum, Int):
        """ Version number for RPM header """
        version = 1
    pad = Nulls(length=4)
    entries = Entries
    payload = Payload

    @CacheAttr
    def entry(self):
        """ Index header entries by tag name """
        entry = Entry(tag=type(self).tag, byteorder=type(self).byteorder)
        return LazyDict((str(ent.tag), ent)
                        for ent in StructArray(self.entries, entry))

    def __getattr__(self, name):
        entry = self.entry[name]
        value = entry.tagtype.fetch(self.payload[entry.offset:], entry.count)
        setattr(self, name, value)
        return value

class RPM(VarStructs, byteorder=2):
    """ RPM layout """
    lead = Lead
    signature = Header
    pad = Struct(member=Pad(align=8))
    header = Header(tag=HeaderTag)
    tail = Struct(member=Tail)

    @CacheAttr
    def payload(self):
        """
        Obtain compression format and archive format from header
        Return archive of memoryview of decompression result
        Add dict keys as necessary for alternate formats
        """
        compressor = dict(xz=lzma, gzip=gzip)[str(self.header.payloadcompressor)]
        archive = dict(cpio=cpio)[str(self.header.payloadformat)]
        return archive.archive(memoryview(compressor.decompress(self.tail)))

    def elves(self):
        """ Generator which yields Elf objects for regular files """
        for member in self.payload:
            if member.isreg():
                try:
                    elf = Elf(member.contents, name=member.name)
                except ElfError:
                    pass
                else:
                    yield elf
