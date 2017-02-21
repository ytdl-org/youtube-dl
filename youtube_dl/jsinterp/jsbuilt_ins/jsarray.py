from __future__ import unicode_literals

from . import undefined
from .base import native_number
from .jsobject import JSObject, JSObjectPrototype
from .jsnumber import JSNumberPrototype


class JSArrayPrototype(JSObjectPrototype):

    def __init__(self, value=None):
        super(JSArrayPrototype, self).__init__()
        self.value = [] if value is None else list(value)
        self.own = {'length': self._length}

    def __str__(self):
        return 'JSArrayPrototype: %s' % self.value

    def __repr__(self):
        return 'JSArrayPrototype(%s, %s)' % (self.value, self._length)

    @property
    def _length(self):
        return len(self.value)

    @staticmethod
    def _constructor(*args):
        return JSArray.construct(*args)

    def _to_string(self):
        return 'array to string'

    def _to_locale_string(self):
        return 'array to locale string'

    def _concat(self, *items):
        return 'array concat'

    def _join(self, sep):
        return 'array join'

    def _pop(self):
        return 'array pop'

    def _push(self, *items):
        return 'array push'

    def _reverse(self):
        return 'array reverse'

    def _shift(self):
        return 'array shift'

    def _slice(self, start, end):
        return 'array slice'

    def _sort(self, cmp):
        return 'array sort'

    def _splice(self, start, delete_count, *items):
        return 'array splice'

    def _unshift(self, *items):
        return 'array unshift'

    def _index_of(self, elem, from_index=0):
        return 'array index of'

    def _last_index_of(self, elem, from_index=None):
        if from_index is None:
            from_index = len(self.value) - 1
        return 'array index of'

    def _every(self, callback, this_arg=None):
        return 'array every'

    def _some(self, callback, this_arg=None):
        return 'array some'

    def _for_each(self, callback, this_arg=None):
        return 'array for_each'

    def _map(self, callback, this_arg=None):
        return 'array map'

    def _filter(self, callback, this_arg=None):
        return 'array filter'

    def _reduce(self, callback, init=None):
        return 'array reduce'

    def _reduce_right(self, callback, init=None):
        return 'array reduce right'

    jsclass = 'Array'
    own = {
        'length': _length,
        'constructor': _constructor,
        'toString': _to_string,
        'toLocaleString': _to_locale_string,
        'concat': _concat,
        'join': _join,
        'pop': _pop,
        'push': _push,
        'reverse': _reverse,
        'shift': _shift,
        'slice': _slice,
        'sort': _sort,
        'splice': _splice,
        'unshift': _unshift,
        'indexOf': _index_of,
        'lastIndexOf': _last_index_of,
        'every': _every,
        'some': _some,
        'forEach': _for_each,
        'map': _map,
        'filter': _filter,
        'reduce': _reduce,
        'reduceRight': _reduce_right
    }


class JSArray(JSObject):

    @staticmethod
    def call(*args):
        return JSArray.construct(*args)

    @staticmethod
    def construct(*args):
        if len(args) == 1:
            if isinstance(args[0], native_number):
                return JSArrayPrototype([undefined] * args[0])
            elif isinstance(args[0], JSNumberPrototype):
                return JSArrayPrototype([undefined] * args[0]._value_of())
        if args:
            return JSArrayPrototype(args)
        else:
            return JSArrayPrototype()

    def _is_array(self, arg):
        return 'array is array'

    name = JSArrayPrototype.jsclass
    own = {
        'length': 1,
        'prototype': JSArrayPrototype(),
        'isArray': _is_array
    }
