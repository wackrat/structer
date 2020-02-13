"""
Enum with keyword-specified variants
"""

from . import NameSpace, Meta

class EnumDict(NameSpace):
    """
    MetaEnum namespace with mapping for member names
    A member is any non-descriptor attribute not present in object.
    Skipping descriptors allows methods to be defined in Enum subclasses.
    """
    def __setitem__(self, key, value):
        if hasattr(object, key) or hasattr(value, '__get__'):
            super().__setitem__(key, value)
        else:
            if key in self.__member__.__mapping__:
                raise KeyError(key)
            if value in self.__member__:
                raise ValueError(value)
            self.__member__[value] = key
            self.__member__.__mapping__[key] = value

    def __init__(self, __mapping__, __member__, __iterable__=(), **kwargs):
        __member__ = type(__member__)(__mapping__={**__member__.__mapping__},
                                      __iterable__=__member__)
        super().__init__(__mapping__, __member__, __iterable__, **kwargs)

class EnumAttr(object):
    """
    Return pre-instantiated member
    """
    def __init__(self, member):
        self.member = member

    def __get__(self, instance, owner):
        return self.member

class MetaEnum(Meta):
    """
    metaclass for Enum
    """
    __namespace__ = EnumDict
    __member__ = NameSpace

    def __init__(cls, name, bases, namespace, **kwargs):
        super().__init__(name, bases, namespace)
        mapping = namespace.__member__.__mapping__
        for name in mapping:
            new = super().__call__(mapping[name])
            new.__name__ = name
            setattr(cls, name, EnumAttr(new))
            mapping[name] = new

    def __call__(cls, *args, **kwargs):
        cls = super().__call__(**kwargs)
        if args:
            member, value = cls.__namespace__.__member__, *args
            try:
                name = member[value]
            except KeyError:
                if isinstance(value, cls):
                    return value
                raise ValueError("%r is not a %s value" % (value, cls.__name__))
            return member.__mapping__[name]
        return cls

    def __getattr__(cls, name):
        try:
            return getattr(cls.__namespace__.__member__, name)
        except AttributeError:
            return super().__getattr__(name)

class Enum(metaclass=MetaEnum):
    """
    Base for enumerated classes
    """
    def __str__(self):
        return self.__name__

    def __repr__(self):
        return '.'.join((type(self).__name__, str(self)))
