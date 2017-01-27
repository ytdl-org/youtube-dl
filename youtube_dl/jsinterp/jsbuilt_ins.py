from __future__ import unicode_literals

from types import FunctionType

from ..compat import compat_str


def _to_js(o, name=None):
    if isinstance(o, JSProtoBase):
        return o
    elif o is None:
        return undefined
    elif isinstance(o, _native_bool):
        return JSBoolean.construct(o)
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


def _type(o):
    if o is undefined:
        return _undefined_type
    elif o is None or o is null:
        return _null_type
    elif isinstance(o, _native_bool) or isinstance(o, JSBooleanPrototype):
        return _boolean_type
    elif isinstance(o, _native_string) or isinstance(o, JSStringPrototype):
        return _string_type
    elif isinstance(o, _native_number) or isinstance(o, JSNumberPrototype):
        return _number_type
    elif isinstance(o, _native_object) or isinstance(o, JSObjectPrototype):
        return _object_type
    return None


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

    def __init__(self, name, own):
        self.name = name
        self.own = own
        self.props = {}

    def __str__(self):
        return '[native code]'

    props = {}


class JSProtoBase(JSBase):

    def __init__(self):
        super(JSProtoBase, self).__init__('', self.props)
        cls = self.__class__
        while cls is not JSProtoBase:
            cls = cls.__base__
            props = cls.props.copy()
            props.update(self.props)
            self.props = props
        self.value = {}

    def __str__(self):
        return ''

    def __get_prop(self, prop):
        result = self.value.get(prop)
        if result is None:
            result = self.own.get(prop)
        if result is None:
            result = self.props.get(prop)
        return result

    @js
    def get_prop(self, prop):
        return self.__get_prop(prop), prop

    @js
    def call_prop(self, prop, *args, **kwargs):
        func = self.__get_prop(prop)
        if isinstance(func, FunctionType):
            return func(self, *args, **kwargs), prop
        elif isinstance(func, staticmethod):
            return func.__func__(*args, **kwargs), prop
        elif isinstance(func, classmethod):
            return func.__func__(self.__class__, *args, **kwargs), prop
        elif isinstance(func, JSBase) and hasattr(func, 'call'):
            return func.call(*args, **kwargs), prop
        else:
            # FIXME instead of prop should return the whole expression
            # needs to use internal exception
            # interpreter should raise JSTypeError
            raise Exception('TypeError: %s is not a function' % prop)


class JSObjectPrototype(JSProtoBase):

    def __init__(self, value=None):
        super(JSObjectPrototype, self).__init__()
        self.value = {} if value is None else value

    @staticmethod
    def _constructor(value=None):
        value = _to_js(value)
        if value is undefined or value is null:
            return JSObjectPrototype()
        elif isinstance(value, JSObjectPrototype):
            return value
        elif isinstance(value, (JSStringPrototype, JSNumberPrototype, JSBooleanPrototype)):
            return to_object(value)

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

    props = {
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
        super(JSObject, self).__init__(self.name, self.props)

    @staticmethod
    def construct(value=None):
        return JSObjectPrototype._constructor(value)

    @staticmethod
    def call(value=None):
        return JSObject.construct(value)

    def _get_prototype_of(self, o):
        return 'object get prototype of'

    def _get_own_property_descriptor(self, o, p):
        return 'object desc'

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

    name = 'Object'
    props = {
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

    def __init__(self, name, body, arguments):
        if name is None and body is None and arguments is None:
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
                body = _to_js(name, body)
                self.body = body.call_prop('toString') if body is not undefined or body is not null else ''
            self.f_name = name
            self.arguments = list(arguments)
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
        if arguments is None:
            body = ''
            arguments = []
        else:
            body = arguments[-1] if arguments else ''
            arguments = arguments[:-1]
        return JSFunctionPrototype('anonymous', body, arguments)

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

    props = {
        'length': 0,
        'constructor': _constructor,
        'toString': _to_string,
        'apply': _apply,
        'call': _call,
        'bind': _bind
    }


class JSFunction(JSObject):

    @staticmethod
    def construct(*args, **kwargs):
        return JSFunctionPrototype._constructor(*args)

    @staticmethod
    def call(*args, **kwargs):
        return JSFunction.construct(*args, **kwargs)

    name = 'Function'
    props = {
        'length': 1,
        'prototype': JSFunctionPrototype(None, None, None)
    }


class JSArrayPrototype(JSObjectPrototype):

    def __init__(self, value=None, length=0):
        super(JSArrayPrototype, self).__init__()
        self.value = [] if value is None else value

    @property
    def _length(self):
        return len(self.value)

    def __str__(self):
        return 'JSArrayPrototype: %s' % self.value

    def __repr__(self):
        return 'JSArrayPrototype(%s, %s)' % (self.value, self._length)

    @staticmethod
    def _constructor(value=None):
        array = JSArrayPrototype(value)
        array.own = {'length': array._length}
        return array

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

    props = {
        'length': 0,
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

    def _is_array(self, arg):
        return 'array is array'

    name = 'Array'
    props = {
        'length': 1,
        'prototype': JSArrayPrototype(),
        'isArray': _is_array
    }


class JSStringPrototype(JSObjectPrototype):
    pass


class JSString(JSObject):
    pass


class JSBooleanPrototype(JSObjectPrototype):
    pass


class JSBoolean(JSObject):
    @staticmethod
    def construct(value=None):
        pass



class JSNumberPrototype(JSObjectPrototype):
    pass


class JSNumber(JSObject):
    pass


undefined = object()
null = object()
true = JSBoolean.construct(True)
false = JSBoolean.construct(False)

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
                                 'Function': JSFunction()})
