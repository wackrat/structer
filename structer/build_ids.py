"""
Fetch Build IDs from ELF core
In --list mode, print two names for each file,
one from the file note, and the other from the link map.
The first file (the executable) is not in the link map.
The names can differ because of symbolic links.
"""

from argparse import ArgumentParser

from . import memmap
from .elf import Core, Elf

def main():
    """ Fetch Build IDs in ELF core """
    parser = ArgumentParser()
    parser.add_argument("--list", action='store_true')
    parser.add_argument("--prefix", type=str, default='')
    parser.add_argument("file")
    args = parser.parse_args()
    core = Core(memmap(args.file), args.file)
    linkmap = {linkmap.addr: linkmap.name for linkmap in core.linkmap}
    for name, addr, build_id in core.build_ids():
        if args.list:
            print("{:016x} {} {} ({})".format(addr, build_id, name, linkmap.get(addr)))
        else:
            try:
                elf_id = Elf(memmap(args.prefix + name), name).build_id()
                assert  elf_id == build_id, "{}: {} != {}".format(name, elf_id, build_id)
            except (AssertionError, FileNotFoundError) as exc:
                print(build_id, exc)
