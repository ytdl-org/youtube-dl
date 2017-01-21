from __future__ import unicode_literals


class JSBase(object):

    _name = ''

    def __init__(self):
        self._props = self.__class__._props.copy()

    def __str__(self):
        return '[native code]'

    _props = {}


class JSProtoBase(JSBase):

    def __init__(self):
        super(JSProtoBase, self).__init__()
        self._value = {}
        cls = self.__class__
        while cls is not JSProtoBase:
            cls = cls.__base__
            props = cls._props.copy()
            props.update(self._props)
            self._props = props

    def __str__(self):
        return ''

    def get_prop(self, prop):
        result = self._value.get(prop)
        return result if result is not None else self._props.get(prop)

    def call_prop(self, prop, *args):
        return self.get_prop(prop)(self, *args)


class JSObjectPrototype(JSProtoBase):

    def __init__(self, value=None):
        super(JSObjectPrototype, self).__init__()
        if value is not None:
            self._value = value

    def _to_string(self):
        return 'object to string'

    def _to_locale_string(self):
        return 'object to locale string'

    def _value_of(self):
        return 'object value of'

    def _has_own_property(self, v):
        return v in self._value

    def _is_prototype_of(self, v):
        return 'object has own prop'

    def _is_property_enumerable(self, v):
        return 'object is property enumerable'

    _props = {
        'constructor': __init__,
        'toString': _to_string,
        'toLocaleString': _to_locale_string,
        'valueOf': _value_of,
        'hasOwnProperty': _has_own_property,
        'isPrototypeOf': _is_prototype_of,
        'propertyIsEnumerable': _is_property_enumerable
    }


class JSObject(JSBase):

    _name = 'Object'

    def _get_prototype_of(self, o):
        return 'object get prototype of'

    def _get_own_property_descriptor(self, o, p):
        return 'object desc'

    def _get_own_property_names(self, o):
        return list(o.value.keys())

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

    _props = {
        'length': 1,
        'prototype': JSObjectPrototype(JSObjectPrototype._props),
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

    def __init__(self, *args):
        body = args[-1] if args else ''
        if isinstance(body, JSBase):
            super(JSFunctionPrototype, self).__init__(value=body._props)
            self._fname = body._name
        else:
            super(JSFunctionPrototype, self).__init__()
            self._fname = 'anonymous'

        # FIXME: JSProtoBase sets body to '' instead of None
        self._body = str(body)
        self._args = [sarg.strip() for arg in args[:-1] for sarg in str(arg).split(',')]
        # TODO check if self._args can be parsed as formal parameter list
        # TODO check if self._body can be parsed as function body
        # TODO set strict
        # TODO throw strict mode exceptions
        # (double argument, "eval" or "arguments" in arguments, function identifier is "eval" or "arguments")

    @property
    def _length(self):
        # FIXME: returns maximum instead of "typical" number of arguments
        # Yeesh, I dare you to find anything like that in the python specification.
        return len(self._args)

    def _to_string(self):
        if self._body is not None:
            body = '\n'
            body += '\t' + self._body if self._body else self._body
        else:
            body = ''
        return 'function %s(%s) {%s\n}' % (self._fname, ', '.join(self._args), body)

    def _apply(self, this_arg, arg_array):
        return 'function apply'

    def _call(self, this_arg, *args):
        return 'function call'

    def _bind(self, this_arg, *args):
        return 'function bind'

    _props = {
        'length': 0,
        'constructor': __init__,
        'toString': _to_string,
        'apply': _apply,
        'call': _call,
        'bind': _bind
    }


class JSFuction(JSObject):

    _name = 'Function'

    _props = {
        'length': 1,
        'prototype': JSFunctionPrototype(JSFunctionPrototype())
    }


class JSArrayPrototype(JSObjectPrototype):

    def __init__(self, value=None, length=0):
        super(JSArrayPrototype, self).__init__()
        self.list = []
        self._value['length'] = self._length

    @property
    def _length(self):
        return len(self.list)

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
            from_index = len(self._value) - 1
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

    _props = {
        'length': 0,
        'constructor': __init__,
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

    _name = 'Array'

    def _is_array(self, arg):
        return 'array is array'

    _props = {
        'length': 1,
        'prototype': JSObjectPrototype(JSArrayPrototype._props),
        'isArray': _is_array
    }

global_obj = JSObjectPrototype({'Object': JSFunctionPrototype(JSObject()),
                                'Array': JSFunctionPrototype(JSArray()),
                                'Function': JSFunctionPrototype(JSFuction())})
