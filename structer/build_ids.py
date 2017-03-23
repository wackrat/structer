#!/usr/bin/python3

"""
Fetch Build IDs from ELF core
In --list mode, print two names for each file,
one from the file note, and the other from the link map.
The first file (the executable) is not in the link map.
The names can differ because of symbolic links.
"""

from argparse import ArgumentParser
import struct

from structer import memmap
from structer.elf import Core, Elf

def hexify(bites):
    """ SHA1 as a string """
    count = len(bites) // 4
    return ("{:08x}"*count).format(*struct.Struct(">{}I".format(count)).unpack(bites))

def main():
    """ Fetch Build IDs in ELF core """
    parser = ArgumentParser()
    parser.add_argument("--list", action='store_true')
    parser.add_argument("--prefix", type=str, default='')
    parser.add_argument("file")
    args = parser.parse_args()
    core = Core(memmap(args.file))
    link_map = {linkmap.addr: linkmap.name for linkmap in core.linkmaps}
    for name, addr, build_id in core.build_ids():
        if args.list:
            print("{:016x} {} {} ({})".format(addr, hexify(build_id), name, link_map.get(addr)))
        else:
            elf_id = Elf(memmap(args.prefix + name)).build_id()
            try:
                assert  elf_id == build_id,\
                "{}: {} != {}".format(name, hexify(elf_id), hexify(build_id))
            except AssertionError as exc:
                print(exc)

if __name__ == '__main__':
    main()
