"""
Access to cpio archive representation via function
Modules for various archive formats can provide a function with a common name.
"""

from stat import S_IFDIR, S_IFREG, S_IFLNK, S_IFIFO, S_IFCHR, S_IFBLK, S_IFSOCK, S_IFMT

from . import CacheAttr
from .data import Bytes, Int, MTime, Pad, Tail, pad, PString
from .named import VarStruct
from .enum import Enum

Number = Int(base=16, length=8)

class FileType(Enum, int):
    """
    File type as obtained from mode bits
    """
    Directory, File, Symlink = S_IFDIR, S_IFREG, S_IFLNK
    FIFO, Cdev, Bdev, Socket = S_IFIFO, S_IFCHR, S_IFBLK, S_IFSOCK

class Cpio(VarStruct):
    """
    Representation of cpio archive
    Iterator yields archive members.
    Each member contains all subsequent members in its tail.
    """
    class magic(Enum, Bytes, length=6):
        """ Magic number for two cpio formats """
        new, crc = b'070701', b'070702'
    inode, mode, uid, gid, nlink = 5*(Number,)
    mtime = MTime(base=16, length=8)
    filesize, major, minor, rmajor, rminor = 5*(Number,)
    name = PString(base=16, length=8)
    check = Number
    pad = Pad(align=4)
    tail = Tail
    @CacheAttr
    def filetype(self):
        """ Extract file type from mode bits """
        return FileType(S_IFMT(self.mode))
    @CacheAttr
    def contents(self):
        """ Slice payload to exclude subsequent content """
        return self.tail[:self.filesize]
    def __iter__(self):
        align = type(self).pad.align
        while len(self.tail) > 0:
            yield self
            size = self.filesize
            self = type(self)(self.tail, size + pad(size, align))
        assert str(self.name) == 'TRAILER!!!', "Truncated archive"

def archive(mem):
    """ Instantiate Cpio on specified memoryview """
    return Cpio(mem)
