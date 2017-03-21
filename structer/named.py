"""
Assign attribute names to tuple indices
"""

import struct
from operator import itemgetter

from . import CacheAttr, base_keywords, NameSpace, NameList, Meta

class TupleDict(dict):
    """
    MetaTuple namespace
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.__names__ = ()

    def __missing__(self, key):
        if hasattr(object, key):
            raise KeyError
        elif key in self.__names__:
            raise KeyError("Duplicate name")
        else:
            self.__names__ += key,

class MetaTuple(type):
    """
    metaclass for named.Tuple
    """
    @classmethod
    def __prepare__(mcs, name, bases, **kwargs):
        return TupleDict(**kwargs)

    def __init__(cls, name, bases, namespace, **kwargs):
        super().__init__(name, bases, namespace)
        cls.__namespace__ = namespace
        for index, key in enumerate(namespace.__names__):
            setattr(cls, key, property(itemgetter(index)))

    def __call__(cls, *args):
        if len(args) != len(cls.__namespace__.__names__):
            raise TypeError("Incorrect argument count")
        return super().__call__(args)

class Tuple(tuple, metaclass=MetaTuple):
    """
    Base class for tuples with attribute names
    """
    def __repr__(self):
        return "{}{}".format(self.__class__.__name__, super().__repr__())

class StructDict(NameSpace):
    """
    MetaStruct namespace
    """
    def __setitem__(self, key, value):
        if isinstance(value, type):
            self.__member__.append(value, key)
        else:
            super().__setitem__(key, value)

    def __call__(self, **kwargs):
        elements = self.__member__(**kwargs)
        if elements is not self.__member__:
            self = type(self)(self.__mapping__, __member__=elements, __iterable__=self)
        return super().__call__(**kwargs)

class StructAttr(object):
    """
    Return element at specified index when accessed from an instance
    Block access when accessed from a class, to defer to __getattr__
    """
    def __init__(self, index):
        self.index = index

    def __get__(self, instance, owner):
        if instance is None:
            raise AttributeError
        else:
            return instance[self.index]

class MetaStruct(Meta):
    """
    metaclass for namedstruct.Struct
    class attributes which are classes are expected to have a __struct_format__ attribute
    """
    @classmethod
    def __prepare__(mcs, name, bases, **kwargs):
        return StructDict(__mapping__=base_keywords(bases), __member__=NameList(), **kwargs)

    def __len__(cls):
        return cls.__struct__.size

    def __init__(cls, name, bases, namespace, **kwargs):
        struct_format = "@<>"[namespace.byteorder] + ''.join(
            init.__struct_format__ for init in namespace.__member__)
        cls.__struct__ = struct.Struct(struct_format)
        cls.__struct_format__ = '{}s'.format(len(cls))
        for key, value in namespace.__member__.__mapping__.items():
            setattr(cls, key, StructAttr(value))
        super().__init__(name, bases, namespace, **kwargs)

class Struct(tuple, metaclass=MetaStruct, byteorder=0):
    """
    tuple subclass with attribute names and initializers from a class declaration
    """
    def __new__(cls, mem, offset=0):
        zipped = zip(cls.__namespace__.__member__,
                     cls.__struct__.unpack_from(mem, offset))
        return super().__new__(cls, (init(value) for (init, value) in zipped))

    __len__ = MetaStruct.__len__

class VarStruct(Struct):
    """
    Struct with callable elements of variable size
    """
    @classmethod
    def __new_iter__(cls, mem, offset):
        return super().__new__(cls, mem, offset)
    @classmethod
    def __init_format__(cls):
        return cls.__struct__.format.decode()
    def __new__(cls, mem, offset=0):
        iterable = cls.__new_iter__(mem, offset)
        struct_format = cls.__init_format__()
        items = []
        offset += struct.Struct(struct_format).size
        for item in iterable:
            if callable(item):
                item = item(mem, offset)
                length = len(item)
                offset += length
                struct_format += '{}s'.format(length)
            items.append(item)
        new = tuple.__new__(cls, items)
        new.__struct__ = struct.Struct(struct_format)
        new.__struct_format__ = '{}s'.format(new.__struct__.size)
        return new

class StructArray(object):
    """
    Contiguous span of named.Struct objects in a memoryview
    """
    def __init__(self, mem, cls):
        self.mem = mem
        self.nbytes = mem.nbytes
        self.cls = cls
        self.itemsize = len(cls)

    @CacheAttr
    def length(self):
        """ Element count """
        return self.nbytes // self.itemsize

    def __len__(self):
        return self.length

    def offset(self, index):
        """ Scale index to byte offset """
        offset = index * self.itemsize
        if offset < 0 or offset >= self.nbytes:
            raise IndexError
        return offset

    def fetch(self, offset):
        """ Instantiate at specified offset """
        return self.cls(self.mem, offset)

    def getitem(self, index):
        """ Fetch from scaled index """
        if index < 0:
            index += self.length
        return self.fetch(self.offset(index))

    def __getitem__(self, index):
        if isinstance(index, slice):
            return self.getslice(index)
        else:
            return self.getitem(index)

    def getslice(self, indices):
        """ Return a generator over the slice range """
        for index in range(*indices.indices(self.length)):
            yield self.getitem(index)

    def __iter__(self):
        offset = 0
        while offset < self.nbytes:
            item = self.fetch(offset)
            offset += len(item)
            yield item

class VarStructArray(StructArray):
    """
    Contiguous span of named.VarStruct objects in a memoryview
    Direct access is provided by an offset cache,
    which is populated on demand by the iterator
    """
    def __init__(self, mem, cls):
        super().__init__(mem, cls)
        self.offsets = []
        self.tail = 0

    @CacheAttr
    def length(self):
        """ Determine element count by populating offset cache """
        while self.tail < self.nbytes:
            next(self)
        return len(self.offsets)

    def offset(self, index):
        """ Fetch accumulated offset from cache; fill cache on demand """
        if index < 0:
            raise IndexError
        try:
            return self.offsets[index]
        except IndexError:
            while self.tail < self.nbytes:
                next(self)
                if len(self.offsets) > index:
                    return self.offsets[index]
            raise IndexError

    def __next__(self):
        offset = self.tail
        if offset >= self.nbytes:
            raise StopIteration
        item = self.fetch(offset)
        size = len(item)
        assert size > 0
        self.offsets.append(offset)
        self.tail += size
        return item
