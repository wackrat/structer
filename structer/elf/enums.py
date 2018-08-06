"""
Enumerated types for ELF
"""
from ..enum import Enum
from ..data import Bytes, Int, Long

class Magic(Enum, Bytes, length=4):
    """ First four bytes of ELF header """
    magic = b'\177ELF'

class WordSize(Enum, Int):
    """ ELF Word size """
    bits32 = 1
    bits64 = 2

class ByteOrder(Enum, Int):
    """ ELF byte order """
    lsb = 1
    msb = 2

class Version(Enum, Int):
    """ ELF version """
    current = 1

class AUXVType(Enum, Long):
    """ ELf auxiliary vector type """
    Null, Ignore, ExecFD, Phdr, PHEnt, PHNum, PageSz, Base = range(0, 8)
    Flags, Entry, NotElf, UID, EUID, GID, EGID, Platform = range(8, 16)
    HWCap, ClkTck, FPUCW, DCacheBsize, ICacheBsize, UCacheBsize = range(16, 22)
    IgnorePPC, Secure, Base_Platform, Random, HWCap2 = range(22, 27)
    ExecFn, SysInfo, SysInfo_EHdr, L1I_CacheShape = range(31, 35)
    L1D_CacheShape, L2_CacheShape, L3_CacheShape = range(35, 38)

class OSABI(Enum, Int):
    """ ELF OS ABI """
    SYSV, HPUX, NetBSD, GNU = range(0, 4)
    Solaris, AIX, Irix, FreeBSD = range(6, 10)
    Tru64, Modesto, OpenBSD = range(10, 13)
    ARM_AEABI, ARM, Standalone = 64, 97, 255

class Type(Enum, Int(length=1)):
    """ ELF type """
    Rel, Exec, Dyn, Core = range(1, 5)

class Machine(Enum, Int(length=1)):
    """ ELF machine """
    M32, Sparc, I386, M68K, M88K = range(1, 6)
    I860, MIPS, S370, MIPS_RS3_LE = range(7, 11)
    PARISC = 15
    VPP500, Sparc32Plus, I960, PPC, PPC64, S390 = range(17, 23)
    V800, FR20, RH32, RCE, ARM, FAKE_ALPHA, SH, SparcV9 = range(36, 44)
    TriCore, ARC, H8_300, H8_300H, H8S, H8_500, IA64, MIPS_X = range(44, 52)
    ColdFire, M68HC12, MMA, PCP, NCPU, NDR1, StarCore, ME16 = range(52, 60)
    ST100, TinyJ, X86_64, PDSP = range(60, 64)
    FX66, ST9Plus, ST7, M68HC16, M68HC11, M68HC08, M68HC05, SVX = range(66, 74)
    ST19, Vax, Cris, Javelen, FirePath, ZSP, MMIX, Huany = range(74, 82)
    Prism, AVR, FR30, D10V, D30V, V850, M32R, MN10300, MN10200, PJ = range(82, 92)
    OpenRISC, ARC_A5, XTensa = range(92, 95)
    Altera_NIOS2, AArch64, TilePro, MicroBlaze, Tilegx = 113, 183, 188, 189, 191

class PType(Enum, Int(length=2)):
    """ ELF segment type """
    Null, Load, Dynamic, Interp, Note, ShLib, Phdr, Tls, Num = range(0, 9)
    GNU_EH_Frame, GNU_Stack, GNU_Relro = range(0x6474e550, 0x6474e553)
    PAX_Flags = 0x65041580

class SType(Enum, Int(length=2)):
    """ Elf section type """
    Null, Prog, Symtab, Strtab, Rela, Hash, Dynamic = range(0, 7)
    Note, Nobits, Rel, Shlib, Dynsym = range(7, 12)
    Init, Fini, Preinit, Group, Shndx = range(14, 19)
    GNUAttributes, GNUHash, GNULiblist, GNUChecksum = range(0x6ffffff5, 0x6ffffff9)
    GNUverdef, GNUverneed, GNUversym = range(0x6ffffffd, 0x70000000)

class Note(Enum, Int(length=2)):
    """ Elf note base class """
    def __eq__(self, other):
        return repr(self) == repr(other)

    def __hash__(self):
        return hash(repr(self))

class DTag(Enum, Long):
    """ Tag values in ELF dynamic section """
    Null, Needed, PLTRelSz, PLTGOT, Hash = range(0, 5)
    StrTab, SymTab, Rela, RelaSz, RelaEnt = range(5, 10)
    StrSz, SymEnt, Init, Fini, SoName = range(10, 15)
    Rpath, Symbolic, Rel, RelSz, RelEnt = range(15, 20)
    PLTRel, Debug, TextRel, JmpRel, BindNow = range(20, 25)
    InitArray, FiniArray, InitArraySz, FiniArraySz, RunPath = range(25, 30)
    Flags, PreInitArray, PreInitArraySz, Num = 30, 32, 33, 34
    GnuHash, TLSDescPLT, TLSDescGOT, GnuConflict, GnuLibList, Config = range(0x6ffffef5, 0x6ffffefb)
    DepAudit, Audit, PLTPad, MoveTab, SymInfo = range(0x6ffffefb, 0x6fffff00)
    VerSym, RelaCount, RelCount, Flags1 = 0x6ffffff0, 0x6ffffff9, 0x6ffffffa, 0x6ffffffb
    VerDef, VerDefNum, VerNeed, VerNeedNum = range(0x6ffffffc, 0x70000000)

class DebugState(Enum, Long):
    """  Enumeration of DebugInfo state values """
    Consistent = 0
    Add = 1
    Delete = 2
