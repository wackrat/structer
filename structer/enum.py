"""
Enum with keyword-specified variants
"""

from . import base_keywords, NameSpace, Meta

class EnumDict(NameSpace):
    """
    MetaEnum namespace with mapping for member names
    A member is any non-descriptor attribute not present in object
    Skipping descriptors allows methods to be defined in Enum subclasses
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

class EnumAttr(object):
    """
    Return member value when accessed from a class
    Return original attribute when accessed from an instance
    This descriptor is used only for namespace conflicts
    """
    def __init__(self, instance, owner):
        self.instance = instance
        self.member = owner

    def __get__(self, instance, owner):
        if instance is None:
            return self.member
        try:
            return self.instance.__get__(instance, owner)
        except AttributeError:
            return self.instance

class MetaEnum(Meta):
    """
    metaclass for Enum
    """
    @classmethod
    def __prepare__(mcs, name, bases, **kwargs):
        return EnumDict(__mapping__=base_keywords(bases), __member__=NameSpace({}), **kwargs)

    def __init__(cls, name, bases, namespace, **kwargs):
        for name in namespace.__member__.__mapping__:
            if hasattr(cls, name):
                member = getattr(namespace.__member__, name)
                setattr(cls, name, EnumAttr(getattr(cls, name), member))
        super().__init__(name, bases, namespace)

    def __call__(cls, *args, **kwargs):
        new = super().__call__(*args, **kwargs)
        if args:
            if new not in cls.__namespace__.__member__:
                raise ValueError("%r is not a %s value" % (new, cls.__name__))
        return new

    def __getattr__(cls, name):
        try:
            return getattr(cls.__namespace__.__member__, name)
        except AttributeError:
            return super().__getattr__(name)

class Enum(metaclass=MetaEnum):
    """
    Base for enumerated classes
    """
    def __repr__(self):
        return '{}.{}'.format(type(self).__name__, self.__namespace__.__member__[self])
