from __future__ import unicode_literals

from .internals import to_string
from .jsobject import JSObject, JSObjectPrototype


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
