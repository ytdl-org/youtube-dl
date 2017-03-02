from __future__ import unicode_literals

from . import true
from .internals import jstype, boolean_type, object_type, to_boolean
from .base import to_js
from .jsobject import JSObject, JSObjectPrototype


class JSBooleanPrototype(JSObjectPrototype):

    def __init__(self, value=None):
        super(JSBooleanPrototype, self).__init__()
        if value is None:
            # prototype
            value = False
        else:
            self.value = value
            self.own = {}

    @staticmethod
    def _constructor(value=None):
        return JSBoolean.construct(value)

    def _to_string(self):
        # TODO find way to test it in other interpreters
        if jstype(self) is boolean_type:
            b = self
        elif jstype(self) is object_type and self.jsclass == 'Boolean':
            b = self.value
        else:
            raise Exception('TypeError')
        return 'true' if b is true else 'false'

    def _value_of(self):
        return 'boolean value of'

    jsclass = 'Boolean'
    own = {
        'constructor': _constructor,
        'toString': _to_string,
        'valueOf': _value_of
    }


class JSBoolean(JSObject):

    @staticmethod
    def call(value=None):
        return to_boolean(to_js(value))

    @staticmethod
    def construct(value=None):
        return JSBooleanPrototype(to_boolean(to_js(value)))

    name = JSBooleanPrototype.jsclass
    own = {
        'length': 1,
        'prototype': JSBooleanPrototype()
    }
