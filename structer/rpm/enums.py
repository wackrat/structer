"""
Enumerated types for RPM
Tag and HeaderTag members are from
https://github.com/rpm-software-management/rpm/blob/master/lib/rpmtag.h
"""
import re
from .. import CacheAttr
from ..data import Int, String, Strings
from ..enum import Enum
from ..named import Struct, StructArray

class Type(Enum, Int(length=1)):
    """ RPM lead type """
    binary, source = 0, 1

class OSnum(Enum, Int(length=1)):
    """ RPM lead osnum """
    linux = 1

class Sig(Enum, Int(length=1)):
    """ RPM lead sig """
    version3 = 5

class Tag(Enum, Int(length=2)):
    """ RPM signature tag """
    signatures, rsa, sha1 = 62, 268, 269
    size, payloadsize = 1000, 1007
    pgp, md5, gpg = 1002, 1004, 1005

class HeaderTag(Enum, Int(length=2)):
    """ RPM header tag """
    immutable, i18ntable = 63, 100
    name, version, release, epoch = range(1000, 1004)
    summary, description, buildtime, buildhost, installtime = range(1004, 1009)
    size, distribution, vendor = range(1009, 1012)
    license, packager, group, changelog, source, patch = range(1014, 1020)
    url, os, arch, prein, postin, preun, postun = range(1020, 1027)
    filesizes, filestates, filemodes = range(1028, 1031)
    rdevs, mtimes, digests, linktos, flags = range(1033, 1038)
    username, groupname, sourcerpm, verify = 1039, 1040, 1044, 1045
    providename, requireflags, requirename, requireversion = range(1047, 1051)
    conflictflags, conflictname, conflictversion = range(1053, 1056)
    excludearch, excludeos, exclusivearch, exclusiveos = range(1059, 1063)
    rpmversion, triggerscripts, triggername = range(1064, 1067)
    triggerversion, triggerflags, triggerindex = range(1067, 1070)
    logtime, logname, logtext = range(1080, 1083)
    preinp, postinp, preunp, postunp = range(1085, 1089)
    buildarchs, obsoletename = 1089, 1090
    triggerscriptprog, docdir, cookie, devices, inodes, langs, prefixes = range(1092, 1099)
    provideflags, provideversion, obsoleteflags, obsoleteversion = range(1112, 1116)
    dirindexes, basenames, dirnames = range(1116, 1119)
    payloadformat, payloadcompressor = 1124, 1125
    optflags, payloadflags, rhnplatform, platform = 1122, 1126, 1131, 1132
    filecolor, fileclass, classdict = range(1140, 1143)
    filedependsx, filedependsn, dependsdict, sourcepkgid, filecontents = range(1143, 1148)
    pretrans, posttrans, pretransprog, posttransprog = range(1151, 1155)
    filecaps, filedigestalgo = 5010, 5011
    ordername, orderversion, orderflags = range(5035, 5038)
    recommendname, recommendversion, recommendflags = range(5046, 5049)
    suggestname, suggestversion, suggestflags = range(5049, 5052)
    encoding, payloaddigest, payloaddigestalgo = 5062, 5092, 5093

class TagType(Enum, Int(length=2)):
    """ RPM header tagtype """
    int0, int1, int2, int3 = range(2, 6)
    string, binary, stringarray, i18n = range(6, 10)
    @CacheAttr
    def fetch(self):
        """ Function indexed by enum name """
        return Tagger(str(self))

INTS = re.compile('^int([0-3])$')

class Tagger(object):
    """ Fetch functions for TagType """
    def __new__(cls, name):
        fetch = getattr(cls, name, None)
        if fetch:
            return fetch
        length = int(INTS.match(name).group(1))
        element = Struct(member=Int(length=length), byteorder=2)
        def ints(payload, count):
            """ StructArray of specified count scaled by element size """
            return StructArray(payload[:len(element) * count], element)
        setattr(cls, name, ints)
        return ints

    def binary(self, count):
        """ Simple memoryview slice """
        return self[:count]

    def string(self, count):
        """ String at start of payload """
        assert count == 1, "string count must be 1"
        return str(String(self))

    def stringarray(self, count):
        """ Strings of specified count at start of payload """
        return Strings(0)(self, 0, count)

    i18n = string
