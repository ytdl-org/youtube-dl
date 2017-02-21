from __future__ import unicode_literals

import re
from math import isnan, isinf, log10
from sys import float_info

from . import undefined, null, true, false
from .base import to_js, native_bool, native_string, native_number, native_object
from .jsobject import JSObjectPrototype
from .jsboolean import JSBooleanPrototype
from .jsstring import JSStringPrototype
from .jsnumber import JSNumberPrototype
from ..jsgrammar import __HEXADECIMAL_RE


def jstype(o):
    if o is undefined:
        return undefined_type
    elif o is None or o is null:
        return null_type
    elif isinstance(o, native_bool) or o is true or o is false:
        return boolean_type
    elif isinstance(o, native_string):
        return string_type
    elif isinstance(o, native_number):
        return number_type
    elif isinstance(o, native_object):
        return object_type
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
            return '-' + to_string(to_js(-ov))
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


undefined_type = object()
null_type = object()
boolean_type = object()
string_type = object()
number_type = object()
object_type = object()
