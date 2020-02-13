"""
Tag values in ELF dynamic section
Subclasses are keyed by enums.Machine name
"""

from ..enum import Enum
from ..data import Long

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

class PPC64(DTag):
    """ DTag for PPC64 """
    GLINK, OPD, OPDSZ, OPT = range(0x70000000, 0x70000004)

class AArch64(DTag):
    """ DTag for AArchc64 """
    VARIANT_PCS = 0x70000005
