from __future__ import unicode_literals

from types import FunctionType

from ...compat import compat_str
from . import undefined
from .jsobject import JSObjectPrototype
from .jsfunction import JSFunctionPrototype
from .jsarray import JSArrayPrototype
from .jsboolean import JSBooleanPrototype
from .jsstring import JSStringPrototype
from .jsnumber import JSNumberPrototype


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
        if isinstance(func, native_function):
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


def to_js(o, name=None):
    if isinstance(o, JSProtoBase):
        return o
    elif o is None:
        return undefined
    elif isinstance(o, native_bool):
        return JSBooleanPrototype(o)
    elif isinstance(o, native_string):
        return JSStringPrototype(o)
    elif isinstance(o, native_number):
        return JSNumberPrototype(o)
    elif isinstance(o, native_object):
        return JSObjectPrototype(o)
    elif isinstance(o, native_function):
        return JSFunctionPrototype(name, o, [])
    elif isinstance(o, JSBase) and hasattr(o, 'call'):
        return JSFunctionPrototype(o.name, o, [])
    elif isinstance(o, native_array):
        return JSArrayPrototype(o)
    else:
        raise Exception('Not allowed conversion %s to js' % type(o))


def js(func):
    def wrapper(*args, **kwargs):
        return to_js(*func(*args, **kwargs))
    return wrapper


native_bool = bool
native_string = compat_str
native_number = (int, float)
native_object = dict
native_array = (list, tuple)
native_function = FunctionType
