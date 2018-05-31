from .base import (
    JSProtoBase, native_bool, native_string, native_number, native_object, native_function, JSBase, native_array
)


def _get_formal_args(func):
    return func.__code__.co_varnames[func.__code__.co_argcount - len((func.__defaults__))]


def to_js(o, name=None):
    from .base import undefined

    from .jsarray import JSArrayPrototype
    from .jsboolean import JSBooleanPrototype
    from .jsfunction import JSFunctionPrototype
    from .jsnumber import JSNumberPrototype
    from .jsobject import JSObjectPrototype
    from .jsstring import JSStringPrototype

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
        return JSFunctionPrototype(name, o, _get_formal_args(o))
    elif isinstance(o, JSBase) and hasattr(o, 'call'):
        return JSFunctionPrototype(o.name, o, _get_formal_args(o.call))
    elif isinstance(o, native_array):
        return JSArrayPrototype(o)
    else:
        raise Exception('Not allowed conversion %s to js' % type(o))


def js(func):
    def wrapper(*args, **kwargs):
        return to_js(*func(*args, **kwargs))
    return wrapper
