#!/usr/bin/python3

from sys import argv
from structer import memmap
from structer.rpm import RPM

def build_ids(name):
    """ Harvest build IDs from members which have them """
    rpm = RPM(memmap(name))
    for elf in rpm.elves():
        yield elf.build_id(), elf.name

if __name__ == '__main__':
    for build_id, name in build_ids(argv[1]):
        print(build_id, name)
