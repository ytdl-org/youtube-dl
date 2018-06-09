from __future__ import unicode_literals

from . import base
from . import jsobject
from . import jsfunction
from . import jsarray
from . import jsboolean
from . import jsstring
from . import jsnumber

from .base import null, undefined
from .jsboolean import false, true


def _eval(code):
    pass


def _parse_int(string, radix):
    pass


def _parse_float(string):
    pass


def _is_nan(number):
    pass


def _is_infinite(number):
    pass


def _decode_uri(encoded_uri):
    pass


def _decode_uri_component(encoded_uri_component):
    pass


def _encode_uri(uri):
    pass


def _encode_uri_component(uri_component):
    pass


global_obj = jsobject.JSObject.construct(
    {'Object': jsobject.JSObject(),
     'Array': jsarray.JSArray(),
     'Function': jsfunction.JSFunction(),
     'String': jsstring.JSString(),
     'Number': jsnumber.JSNumber(),
     'false': jsboolean.false,
     'true': jsboolean.true,
     'null': base.null,
     'undefined': base.undefined
     })
