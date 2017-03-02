from __future__ import unicode_literals

from . import null, undefined
from .base import JSProtoBase, to_js, js, JSBase
from .internals import to_object
from .jsboolean import JSBooleanPrototype
from .jsnumber import JSNumberPrototype
from .jsstring import JSStringPrototype


class JSObjectPrototype(JSProtoBase):

    def __init__(self, value=None):
        super(JSObjectPrototype, self).__init__()
        if value is not None:
            self.props.update(self.own)
            self.own = self.value = value

    @staticmethod
    def _constructor(value=None):
        return JSObject.construct(value)

    def _to_string(self):
        return 'object to string'

    def _to_locale_string(self):
        return 'object to locale string'

    def _value_of(self):
        return 'object value of'

    def _has_own_property(self, v):
        return v in self.own

    def _is_prototype_of(self, v):
        return 'object has own prop'

    def _is_property_enumerable(self, v):
        return 'object is property enumerable'

    jsclass = 'Object'
    own = {
        'constructor': _constructor,
        'toString': _to_string,
        'toLocaleString': _to_locale_string,
        'valueOf': _value_of,
        'hasOwnProperty': _has_own_property,
        'isPrototypeOf': _is_prototype_of,
        'propertyIsEnumerable': _is_property_enumerable
    }


class JSObject(JSBase):

    def __init__(self):
        super(JSObject, self).__init__(self.name)

    @staticmethod
    def call(value=None):
        if value is null or value is undefined or value is None:
            return JSObject.construct(value)
        return to_object(to_js(value))

    @staticmethod
    def construct(value=None):
        value = to_js(value)
        # TODO set [[Prototype]], [[Class]], [[Extensible]], internal methods
        if value is undefined or value is null:
            return JSObjectPrototype({})
        elif isinstance(value, JSObjectPrototype):
            return value
        elif isinstance(value, (JSStringPrototype, JSNumberPrototype, JSBooleanPrototype)):
            return to_object(value)

    def _get_prototype_of(self, o):
        return 'object get prototype of'

    def _get_own_property_descriptor(self, o, p):
        return 'object desc'

    @js
    def _get_own_property_names(self, o):
        return list(o.own.keys())

    def _create(self, o, props=None):
        return 'object create'

    def _define_property(self, o, p, attr):
        return 'object define prop'

    def _define_properties(self, o, props):
        return 'object define properties'

    def _seal(self, o):
        return 'object seal'

    def _freeze(self, o):
        return 'object freeze'

    def _prevent_extensions(self, o):
        return 'object prevent extension'

    def _is_sealed(self, o):
        return 'object is sealed'

    def _is_frozen(self, o):
        return 'object is frozen'

    def _is_extensible(self, o):
        return 'object is extensible'

    def _keys(self, o):
        return 'object keys'

    name = JSObjectPrototype.jsclass
    own = {
        'length': 1,
        'prototype': JSObjectPrototype(),
        'getPrototypeOf': _get_prototype_of,
        'getOwnPropertyDescriptor': _get_own_property_descriptor,
        'getOwnPropertyNames': _get_own_property_names,
        'create': _create,
        'defineProperty': _define_property,
        'defineProperties': _define_properties,
        'seal': _seal,
        'freeze': _freeze,
        'preventExtensions': _prevent_extensions,
        'isSealed': _is_sealed,
        'isFrozen': _is_frozen,
        'isExtensible': _is_extensible,
        'keys': _keys
    }
