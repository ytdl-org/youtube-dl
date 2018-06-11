from __future__ import unicode_literals

from ..utils import ExtractorError
from .jsbuilt_ins.base import isprimitive


class Context(object):
    def __init__(self, variables=None, ended=False):
        super(Context, self).__init__()
        self.ended = ended
        self.no_in = True
        self.local_vars = {}
        if variables is not None:
            for k, v in dict(variables).items():
                # XXX validate identifiers
                self.local_vars[k] = Reference(v, (self.local_vars, k))


class Reference(object):
    def __init__(self, value, parent_key=None):
        super(Reference, self).__init__()
        self.value = value
        if parent_key is not None:
            self.parent, self.name = parent_key
        else:
            self.parent = self.name = None

    def getvalue(self, deep=False):
        value = self.value
        if deep:
            if isinstance(self.value, (list, tuple)):
                # TODO test nested arrays
                value = [elem if isprimitive(elem) else elem.getvalue() for elem in self.value]
            elif isinstance(self.value, dict):
                value = {}
                for key, prop in self.value.items():
                    value[key] = prop.getvalue()

        return value

    def putvalue(self, value):
        if self.parent is None:
            raise ExtractorError('Trying to set a read-only reference')
        if not hasattr(self.parent, '__setitem__'):
            raise ExtractorError('Unknown reference')
        self.parent.__setitem__(self.name, Reference(value, (self.parent, self.name)))
        self.value = value
        return value

    def __repr__(self):
        if self.parent is not None:
            parent, key = self.parent
            return '<Reference value: %s, parent: %s@(0x%x), key: %s>' % (
                str(self.value), parent.__class__.__name__, id(parent), key)
        return '<Reference value: %s, parent: %s>' % (self.value, None)

    def __eq__(self, other):
        if isinstance(other, Reference):
            return self.parent is other.parent and self.name == other.name
        return False

    def __ne__(self, other):
        return not self.__eq__(other)