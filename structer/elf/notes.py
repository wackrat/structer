""" Map note names to Enum subclasses """

from .enums import Note

class GNU(Note):
    """ ELF note type """
    ABI_Tag, HWCap, Build_ID, Gold_Version = range(1, 5)

class CORE(Note):
    """ ELF core note type """
    PRStatus, FPRegset, PRPSInfo, PRXreg = range(1, 5)
    Platform, Auxv, GWindows, ASRS = range(5, 9)
    PStatus = 10
    PSInfo, PRCred, UTSName, LWPStatus, LWPSInfo = range(13, 18)
    PRFPXreg, SigInfo, File, PRXFPreg = 20, 0x53494749, 0x46494c45, 0x46e62b7f
    PPC_VMX, PPC_SPE, PPC_VSX, PPC_TAR = range(0x100, 0x104)
    PPC_PPR, PPC_DSCR, PPC_EBB, PPC_PMU = range(0x104, 0x108)
    PPC_TM_CGPR, PPC_TM_CFPR, PPC_TM_CVMX, PPC_TM_CVSX = range(0x108, 0x10c)
    PPC_TM_SPR, PPC_TM_CTAR, PPC_TM_CPPR, PPC_TM_CDSCR = range(0x10c, 0x110)
    I386_TLS, I386_IOPerm, IX86_XState = range(0x200, 0x203)
    S390_High_GPRS, S390_Timer, S390_TODCmp, S390_TODPreg, S390_CTRS = range(0x300, 0x305)
    S390_Prefix, S390_Last_Break, S390_System_Call, S390_TDB = range(0x305, 0x309)
    ARM_VFP, ARM_TLS, ARM_HW_Break, ARM_HW_Watch = range(0x400, 0x404)
    ARM_System_Call, ARM_SVE, ARM_PAC_Mask, ARM_PACA_Keys = range(0x404, 0x408)

LINUX = CORE

class Linux(Note):
    """ Note from vdso """
    Version = 0

class stapsdt(Note):
    """ SDT probe """
    version3 = 3

class Go(Note):
    """ Note from golang binary """
    PGKList, ABIHash, GoDeps, BuildID = range(1, 5)
