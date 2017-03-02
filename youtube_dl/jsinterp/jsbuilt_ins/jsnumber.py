from __future__ import unicode_literals

from .internals import jstype, number_type, to_number
from .base import to_js
from .jsobject import JSObject, JSObjectPrototype


class JSNumberPrototype(JSObjectPrototype):

    def __init__(self, value=None):
        super(JSNumberPrototype, self).__init__()
        if value is None:
            # prototype
            value = 0
        else:
            self.value = value
            self.own = {}

    @staticmethod
    def _constructor(value=None):
        return JSNumber.construct(value)

    def _to_string(self, radix=None):
        pass

    def _to_locale_string(self):
        pass

    def _value_of(self):
        if jstype(self.value) is not number_type or isinstance(self.value, JSNumberPrototype):
            # TODO find way to test it in other interpreters
            raise Exception('TypeError')
        return self.value

    def _to_fixed(self, frac_digits):
        return 'Number toFixed'

    def _to_exponential(self, frac_digits):
        return 'Number toExponential'

    def _to_precision(self, prec):
        return 'Number toPrecision'

    jsclass = 'Number'
    own = {
        'constructor': _constructor,
        'toString': _to_string,
        'toLocaleString': _to_locale_string,
        'valueOf': _value_of,
        'toFixed': _to_fixed,
        'toExponential': _to_exponential,
        'toPrecision': _to_precision
    }


class JSNumber(JSObject):
    @staticmethod
    def call(value=None):
        return to_number(to_js(value)) if value is not None else 0

    @staticmethod
    def construct(value=None):
        return JSNumberPrototype(to_number(to_js(value)) if value is not None else 0)

    name = JSNumberPrototype.jsclass
    own = {
        'length': 1,
        'prototype': JSNumberPrototype(),
        'MAX_VALUE': 1.7976931348623157 * 10 ** 308,
        'MIN_VALUE': 5 * 10 ** (-324),
        'NAN': float('nan'),
        'NEGATIVE_INFINITY': float('-inf'),
        'POSITIVE_INFINITY': float('inf'),
    }
