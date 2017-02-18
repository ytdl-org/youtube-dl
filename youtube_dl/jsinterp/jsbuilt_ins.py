from __future__ import unicode_literals

import re

from math import isnan, isinf, log10
from sys import float_info
from types import FunctionType

from ..compat import compat_str
from .jsgrammar import __HEXADECIMAL_RE


def _to_js(o, name=None):
    if isinstance(o, JSProtoBase):
        return o
    elif o is None:
        return undefined
    elif isinstance(o, _native_bool):
        return JSBooleanPrototype(o)
    elif isinstance(o, _native_string):
        return JSStringPrototype(o)
    elif isinstance(o, _native_number):
        return JSNumberPrototype(o)
    elif isinstance(o, _native_object):
        return JSObjectPrototype(o)
    elif isinstance(o, _native_function):
        return JSFunctionPrototype(name, o, [])
    elif isinstance(o, JSBase) and hasattr(o, 'call'):
        return JSFunctionPrototype(o.name, o, [])
    elif isinstance(o, _native_array):
        return JSArrayPrototype(o)
    else:
        raise Exception('Not allowed conversion %s to js' % type(o))


def js(func):
    def wrapper(*args, **kwargs):
        return _to_js(*func(*args, **kwargs))
    return wrapper


def jstype(o):
    if o is undefined:
        return _undefined_type
    elif o is None or o is null:
        return _null_type
    elif isinstance(o, _native_bool) or o is true or o is false:
        return _boolean_type
    elif isinstance(o, _native_string):
        return _string_type
    elif isinstance(o, _native_number):
        return _number_type
    elif isinstance(o, _native_object):
        return _object_type
    return None


def to_primitive(o, hint=None):
    # TODO to_primitive
    return o


def to_boolean(o):
    if o is undefined or o is null:
        return false
    elif isinstance(o, JSBooleanPrototype):
        return o.value
    elif isinstance(o, JSNumberPrototype):
        return true if o.value and not isnan(o.value) else false
    elif isinstance(o, JSStringPrototype):
        return true if o.value else false
    elif isinstance(o, JSObjectPrototype):
        return true
    else:
        raise Exception('Failed to convert type %s to Boolean (not specified)' % type(o))


def to_number(o):
    if o is undefined:
        return float('nan')
    elif o is null or isinstance(o, JSBooleanPrototype) and o.value is false:
        return 0
    elif isinstance(o, JSBooleanPrototype) and o.value is true:
        return 1
    elif isinstance(o, JSStringPrototype):
        _STR_FLOAT_RE = r'(?:(?:[0-9]+(?:\.[0-9]*)?)|(?:\.[0-9]+))(?:[eE][+-]?[0-9]+)?'
        m = re.match(r'^[\s\n]*(?P<value>(?:[+-]*(?:Infinity|%(float)s))|%(hex)s)?[\s\n]*$' % {'float': _STR_FLOAT_RE,
                                                                                               'hex': __HEXADECIMAL_RE},
                     o.value)
        if m:
            v = m.group('value')
            if v:
                s = 1 if v.startswith('+') or v.startswith('-') else 0
                if v[s:] == 'Infinity':
                    return float(v[:s] + 'inf')  # 10 ** 10000 according to spec
                elif v[s:].isdigit():
                    return int(v)
                elif v.startswith('0x') or v.startswith('0X'):
                    return int(v, 16)
                else:
                    return float(v)
            else:
                return 0
        else:
            return float('nan')

    elif isinstance(o, JSObjectPrototype):
        prim_value = to_primitive(o, 'Number')
        return to_number(prim_value)
    else:
        raise Exception('Failed to convert type %s to Number (not specified)' % type(o))


def to_integer(o):
    number = to_number(o)
    if isnan(number):
        return 0
    elif isinf(number) or number == 0:
        return number
    return int(number)  # equivalent to: int(copysign(floor(abs(number)), number))


def to_int32(o):
    number = to_number(o)
    if isnan(number) or isinf(number) or number == 0:
        return 0
    pos_int = int(number)
    int32 = pos_int % 2 ** 32
    return int32 if int32 < 2 ** 31 else int32 - 2 ** 32


def to_uint32(o):
    number = to_number(o)
    if isnan(number) or isinf(number) or number == 0:
        return 0
    pos_int = int(number)
    int32 = pos_int % 2 ** 32
    return int32


def to_uint16(o):
    number = to_number(o)
    if isnan(number) or isinf(number) or number == 0:
        return 0
    pos_int = int(number)
    int16 = pos_int % 2 ** 16
    return int16


def to_string(o):
    if o is undefined:
        return 'undefined'
    elif o is null:
        return 'null'
    elif isinstance(o, JSBooleanPrototype):
        if o is true:
            return 'true'
        elif o is false:
            return 'false'
    elif isinstance(o, JSNumberPrototype):
        ov = o.value
        if isnan(ov):
            return 'NaN'
        elif ov == 0.0:
            return '0'
        elif ov < 0:
            return '-' + to_string(_to_js(-ov))
        elif isinf(ov):
            return 'Infinity'
        else:
            # numerically unstable example: 3333330000000000000.3 or 3.3333300000000000003e+20
            n = log10(ov) + 1
            n = int(n)
            k = 1

            while True:
                exp = 10 ** (k - n)
                s = int(ov * exp)
                if abs(ov * exp - s) < float_info.epsilon:
                    break
                k += 1

            if s % 10 == 0:
                s //= 10
            m = '%d' % s

            if k <= n <= 21:
                return m[:k] + '0' * (n - k)
            elif 0 < n <= 21:
                return m[:n] + '.' + m[n:k]
            elif -6 < n <= 0:
                return '0.' + '0' * -n + m[:k]
            elif k == 1:
                return m[0] + 'e%+d' % (n - 1)
            else:
                return m[0] + '.' + m[:k] + 'e%+d' % (n - 1)

    elif isinstance(o, JSObjectPrototype):
        prim_value = to_primitive(o, 'String')
        return to_string(prim_value)
    else:
        raise Exception('Failed to convert type %s to String (not specified)' % type(o))


def to_object(o):
    if o is undefined or o is null:
        raise Exception('TypeError: Cannot convert undefined or null to object')
    elif isinstance(o, JSBooleanPrototype):
        return JSBooleanPrototype(o)
    elif isinstance(o, JSNumberPrototype):
        return JSNumberPrototype(o)
    elif isinstance(o, JSStringPrototype):
        return JSStringPrototype(o)
    elif isinstance(o, JSObjectPrototype):
        return o


class JSBase(object):

    def __init__(self, name):
        self.name = name
        self.props = {}

    own = {}


class JSProtoBase(JSBase):

    def __init__(self):
        super(JSProtoBase, self).__init__('')
        cls = self.__class__
        while cls.__base__ is not JSProtoBase:
            cls = cls.__base__
            props = cls.own.copy()
            props.update(self.props)
            self.props = props
        self.value = {}

    def get_prop(self, prop):
        result = self.value.get(prop) if hasattr(self.value, 'get') else None
        if result is None:
            result = self.own.get(prop)
        if result is None:
            result = self.props.get(prop)
        return result

    def call_prop(self, prop, *args, **kwargs):
        func = self.get_prop(prop)
        if isinstance(func, _native_function):
            return func(self, *args, **kwargs)
        elif isinstance(func, staticmethod):
            return func.__func__(*args, **kwargs)
        elif isinstance(func, classmethod):
            return func.__func__(self.__class__, *args, **kwargs)
        elif isinstance(func, JSBase) and hasattr(func, 'call'):
            return func.call(*args, **kwargs)
        else:
            # FIXME instead of prop should return the whole expression
            # needs to use internal exception
            # interpreter should raise JSTypeError
            raise Exception('TypeError: %s is not a function' % prop)

    jsclass = ''


class JSObjectPrototype(JSProtoBase):

    def __init__(self, value=None):
        super(JSObjectPrototype, self).__init__()
        self.value = {} if value is None else value

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
        return to_object(_to_js(value))

    @staticmethod
    def construct(value=None):
        value = _to_js(value)
        # TODO set [[Prototype]], [[Class]], [[Extensible]], internal methods
        if value is undefined or value is null:
            return JSObjectPrototype()
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


class JSFunctionPrototype(JSObjectPrototype):

    def __init__(self, name, body, formal_args):
        if name is None and body is None and formal_args is None:
            # prototype
            super(JSFunctionPrototype, self).__init__()
            self.f_name = ''
            self.body = ''
        else:
            if isinstance(body, JSBase):
                super(JSFunctionPrototype, self).__init__(body.own)
                self.body = '[native code]'
            elif isinstance(body, _native_function):
                super(JSFunctionPrototype, self).__init__()
                self.body = '[native code]'
            else:
                super(JSFunctionPrototype, self).__init__()
                body = _to_js(body)
                self.body = to_string(body) if body is not undefined or body is not null else ''
            self.f_name = name
            self.arguments = list(formal_args)
            # FIXME: JSProtoBase sets body to '' instead of None
            # TODO check if self._args can be parsed as formal parameter list
            # TODO check if self._body can be parsed as function body
            # TODO set strict
            # TODO throw strict mode exceptions
            # (double argument, "eval" or "arguments" in arguments, function identifier is "eval" or "arguments")

    @property
    def _length(self):
        # Yeesh, I dare you to find anything like that in the python specification.
        return len([arg for arg, init in self.arguments if init is not None])

    @staticmethod
    def _constructor(arguments=None):
        return JSFunction.construct(arguments)

    def _to_string(self):
        if self.body is not None:
            body = '\n'
            body += '\t' + self.body if self.body else self.body
        else:
            body = ''
        return 'function %s(%s) {%s\n}' % (
            self.f_name,
            ', '.join(arg if init is None else arg + '=' + init for arg, init in self.arguments),
            body)

    def _apply(self, this_arg, arg_array):
        return 'function apply'

    def _call(self, this_arg, *args):
        return 'function call'

    def _bind(self, this_arg, *args):
        return 'function bind'

    jsclass = 'Function'
    own = {
        'length': 0,
        'constructor': _constructor,
        'toString': _to_string,
        'apply': _apply,
        'call': _call,
        'bind': _bind
    }


class JSFunction(JSObject):

    @staticmethod
    def call(formal_args=None):
        return JSFunction.construct(formal_args)

    @staticmethod
    def construct(formal_args=None):
        if formal_args is None:
            body = ''
            formal_args = []
        else:
            body = formal_args[-1] if formal_args else ''
            formal_args = formal_args[:-1]
        return JSFunctionPrototype('anonymous', body, formal_args)

    name = JSFunctionPrototype.jsclass
    own = {
        'length': 1,
        'prototype': JSFunctionPrototype(None, None, None)
    }


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
            if isinstance(args[0], _native_number):
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


class JSStringPrototype(JSObjectPrototype):

    def __init__(self, value=None):
        if value is None:
            # prototype
            value = ''
        super(JSStringPrototype, self).__init__(value)

    @property
    def _length(self):
        return len(self.value)

    @staticmethod
    def _constructor(value=None):
        return JSString.construct(value)

    def _to_string(self):
        return self.value

    def _value_of(self):
        return self.value

    def _char_at(self, pos):
        return 'string char at'

    def _char_code_at(self, pos):
        return 'string char code at'

    def _concat(self, *args):
        return 'string concat'

    def _index_of(self, search, pos):
        return 'string index of'

    def _last_index_of(self, search, pos):
        return 'string last index of'

    def _locale_compare(self, that):
        return 'string locale compare'

    def _match(self, regexp):
        return 'string match'

    def _replace(self, search, value):
        return 'string replace'

    def _search(self, regexp):
        return 'string search'

    def _slice(self, start, end):
        return 'string slice'

    def _split(self, sep):
        return 'string split'

    def _substring(self, start, end):
        return 'string substring'

    def _to_lower_case(self):
        return 'string to lower case'

    def _to_local_lower_case(self):
        return 'string to local lower case'

    def _to_upper_case(self):
        return 'string to upper case'

    def _to_local_upper_case(self):
        return 'string to local upper case'

    def _trim(self):
        return 'string trim'

    jsclass = 'String'
    own = {
        'length': _length,
        'constructor': _constructor,
        'toString': _to_string,
        'valueOf': _value_of,
        'charAt': _char_at,
        'charCodeAt': _char_code_at,
        'concat': _concat,
        'indexOf': _index_of,
        'lastIndexOf': _last_index_of,
        'localeCompare': _locale_compare,
        'match': _match,
        'replace': _replace,
        'search': _search,
        'slice': _slice,
        'split': _split,
        'substring': _substring,
        'toLowerCase': _to_lower_case,
        'toLocalLowerCase': _to_local_lower_case,
        'toUpperCase': _to_upper_case,
        'toLocalUpperCase': _to_local_upper_case,
        'trim': _trim
    }


class JSString(JSObject):

    @staticmethod
    def call(value=None):
        return '' if value is None else to_string(value)

    @staticmethod
    def construct(value=None):
        return JSStringPrototype('' if value is None else to_string(value))

    def _from_char_code(self, *args):
        return 'String from char code'

    name = JSStringPrototype.jsclass
    own = {
        'length': 1,
        'prototype': JSStringPrototype(),
        'fromCharCode': _from_char_code
    }


class JSBooleanPrototype(JSObjectPrototype):

    def __init__(self, value=None):
        if value is None:
            # prototype
            value = False
        super(JSBooleanPrototype, self).__init__(value)

    @staticmethod
    def _constructor(value=None):
        return JSBoolean.construct(value)

    def _to_string(self):
        # TODO find way to test it in other interpreters
        if jstype(self) is _boolean_type:
            b = self
        elif jstype(self) is _object_type and self.jsclass == 'Boolean':
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
        return to_boolean(value)

    @staticmethod
    def construct(value=None):
        return JSBooleanPrototype(to_boolean(_to_js(value)))

    name = JSBooleanPrototype.jsclass
    own = {
        'prototype': JSBooleanPrototype()
    }


class JSNumberPrototype(JSObjectPrototype):
    # TODO Number object
    pass


class JSNumber(JSObject):
    # TODO Number class
    pass


undefined = JSBase('undefined')
null = JSBase('null')
true = JSBooleanPrototype(True)
false = JSBooleanPrototype(False)

_native_bool = bool
_native_string = compat_str
_native_number = (int, float)
_native_object = dict
_native_array = (list, tuple)
_native_function = FunctionType

_undefined_type = object()
_null_type = object()
_boolean_type = object()
_string_type = object()
_number_type = object()
_object_type = object()

global_obj = JSObject.construct({'Object': JSObject(),
                                 'Array': JSArray(),
                                 'Function': JSFunction(),
                                 'String': JSString()
                                 })
