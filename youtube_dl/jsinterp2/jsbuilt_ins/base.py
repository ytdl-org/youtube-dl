from __future__ import unicode_literals

from types import FunctionType

from ...compat import compat_str


class JSBase(object):

    def __init__(self, name):
        self.name = name
        self.props = {}

    own = {}


undefined = JSBase('undefined')
null = JSBase('null')


class JSProtoBase(JSBase):

    def __init__(self):
        super(JSProtoBase, self).__init__('')
        cls = self.__class__
        while cls.__base__ is not JSProtoBase:
            props = cls.own.copy()
            props.update(self.props)
            self.props = props
            cls = cls.__base__
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


native_bool = bool
native_string = compat_str
native_number = (int, float)
native_object = dict
native_array = (list, tuple)
native_function = FunctionType


def isprimitive(value):
    return (isinstance(value, (native_bool, native_string, native_number, native_object, native_array, native_function))
            or value is None)
