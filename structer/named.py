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
        if isinstance(value, type) and self.member is None:
            self.__member__.append(value(**self.__mapping__), key)
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
    Return element type from namespace when accessed from a class
    """
    def __init__(self, index):
        self.index = index

    def __get__(self, instance, owner):
        if instance is None:
            return owner.__namespace__.__member__[self.index]
        else:
            return instance[self.index]

class MetaStruct(Meta):
    """
    metaclass for named.Struct
    class attributes which are classes are expected to have a __struct_format__ attribute
    """
    @classmethod
    def __prepare__(mcs, name, bases, **kwargs):
        return StructDict(__mapping__=base_keywords(bases), __member__=NameList(), **kwargs)

    def __len__(cls):
        return cls.__struct__.size

    def __init__(cls, name, bases, namespace, **kwargs):
        if namespace.member and not namespace.__member__:
            namespace.__member__ = NameList(__iterable__=[namespace.member], member=0)
        cls.__prefix__ = "@<>"[namespace.byteorder]
        struct_format = cls.__prefix__ + ''.join(
            init.__struct_format__ for init in namespace.__member__)
        cls.__len__ = type(cls).__len__
        cls.__struct__ = struct.Struct(struct_format)
        cls.__struct_format__ = '{}s'.format(len(cls))
        for key, value in namespace.__member__.__mapping__.items():
            setattr(cls, key, StructAttr(value))
        super().__init__(name, bases, namespace, **kwargs)

class Struct(tuple, metaclass=MetaStruct, byteorder=0, member=None):
    """
    tuple subclass with attribute names and initializers from a class declaration
    """
    def __new__(cls, mem, offset=0):
        if cls.member is None:
            zipped = zip(cls.__namespace__.__member__,
                         cls.__struct__.unpack_from(mem, offset))
            return super().__new__(cls, (init(value) for (init, value) in zipped))
        else:
            item, = cls.__struct__.unpack_from(mem, offset)
            item = cls.member(item)
            return item(mem, offset + len(cls)) if callable(item) else item

    __getattr__ = Meta.__getattr__

class VarStruct(Struct):
    """
    Struct with callable elements of variable size
    """
    @classmethod
    def __new_iter__(cls, mem, offset):
        """ Use tuple.__iter__ to allow custom __iter__ method """
        return tuple.__iter__(super().__new__(cls, mem, offset))
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

class VarStructs(VarStruct):
    """
    A VarStruct with multiple VarStruct members
    """
    @classmethod
    def __init_format__(cls):
        return cls.__prefix__
    @classmethod
    def __new_iter__(cls, mem, offset):
        return cls.__namespace__.__member__

class StructArray(object):
    """
    Contiguous span of named.Struct objects in a memoryview
    """
    def __init__(self, mem, cls):
        self.mem = mem
        self.cls = cls

    def fetch(self, offset):
        """ Instantiate at specified offset """
        return self.cls(self.mem, offset)

    @CacheAttr
    def offset(self):
        """ Scale index to byte offset """
        return range(0, self.mem.nbytes, len(self.cls))

    def __len__(self):
        return len(self.offset)

    def __getitem__(self, index):
        if isinstance(index, slice):
            return tuple(self)[index]
        else:
            return self.fetch(self.offset[index])

    def __iter__(self):
        offset = 0
        while offset < self.mem.nbytes:
            item = self.fetch(offset)
            yield item
            offset += len(item)

def offsets(sequence, offset=0):
    """ Offset of each element of a contiguous sequence """
    for item in sequence:
        yield offset
        offset += len(item)

class VarStructArray(StructArray):
    """
    Contiguous span of named.VarStruct objects in a memoryview
    Direct access is provided by an offset cache.
    """
    @CacheAttr
    def offset(self):
        """ Offset cache """
        return tuple(offsets(self))
