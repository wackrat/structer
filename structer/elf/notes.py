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
    PPC_VMX, PPC_SPE, PPC_VSX = range(0x100, 0x103)
    I386_TLS, I386_IOPerm, IX86_XState = range(0x200, 0x203)
    S390_High_GPRS, S390_Timer, S390_TODCmp, S390_TODPreg, S390_CTRS = range(0x300, 0x305)
    S390_Prefix, S390_Last_Break, S390_System_Call, S390_TDB = range(0x305, 0x309)
    ARM_VFP, ARM_TLS, ARM_HW_Break, ARM_HW_Watch = range(0x400, 0x404)

LINUX = CORE

class Linux(Note):
    """ Note from vdso """
    Version = 0

class stapsdt(Note):
    """ SDT probe """
    version3 = 3