from __future__ import unicode_literals

import re
import operator

from ..utils import ExtractorError
from .jsgrammar import (
    COMMENT_RE,
    TOKENS_RE,
    PUNCTUATIONS_RE,
    LOGICAL_OPERATORS_RE,
    UNARY_OPERATORS_RE,
    RELATIONS_RE,
    ASSIGN_OPERATORS_RE,
    OPERATORS_RE
)


_PUNCTUATIONS = {
    '{': 'copen',
    '}': 'cclose',
    '(': 'popen',
    ')': 'pclose',
    '[': 'sopen',
    ']': 'sclose',
    '.': 'dot',
    ';': 'end',
    ',': 'comma',
    '?': 'hook',
    ':': 'colon'
}
_LOGICAL_OPERATORS = {
    '&&': ('and', lambda cur, right: cur and right),
    '||': ('or', lambda cur, right: cur or right)
}
_UNARY_OPERATORS = {
    '++': ('inc', lambda cur: cur + 1),
    '--': ('dec', lambda cur: cur - 1),
    '!': ('not', operator.not_),
    '~': ('bnot', lambda cur: cur ^ -1),
    # XXX define these operators
    'delete': ('del', None),
    'void': ('void', None),
    'typeof': ('type', lambda cur: type(cur))
}
_RELATIONS = {
    '<': ('lt', operator.lt),
    '>': ('gt', operator.gt),
    '<=': ('le', operator.le),
    '>=': ('ge', operator.ge),
    # XXX check python and JavaScript equality difference
    '==': ('eq', operator.eq),
    '!=': ('ne', operator.ne),
    '===': ('seq', lambda cur, right: cur == right and type(cur) == type(right)),
    '!==': ('sne', lambda cur, right: not cur == right or not type(cur) == type(right))
}
_OPERATORS = {
    '|': ('bor', operator.or_),
    '^': ('bxor', operator.xor),
    '&': ('band', operator.and_),
    # NOTE convert to int before shift float
    '>>': ('rshift', operator.rshift),
    '<<': ('lshift', operator.lshift),
    '>>>': ('urshift', lambda cur, right: cur >> right if cur >= 0 else (cur + 0x100000000) >> right),
    '-': ('sub', operator.sub),
    '+': ('add', operator.add),
    '%': ('mod', operator.mod),
    '/': ('div', operator.truediv),
    '*': ('mul', operator.mul)
}
_ASSIGN_OPERATORS = dict((op + '=', ('set_%s' % token[0], token[1])) for op, token in _OPERATORS.items())
_ASSIGN_OPERATORS['='] = ('set', lambda cur, right: right)

_operator_lookup = {
    'op': _OPERATORS,
    'aop': _ASSIGN_OPERATORS,
    'uop': _UNARY_OPERATORS,
    'lop': _LOGICAL_OPERATORS,
    'rel': _RELATIONS
}
# only to check ids
_reserved_words = ('break', 'case', 'catch', 'continue', 'debugger', 'default', 'delete', 'do', 'else', 'finally',
                   'for', 'function', 'if', 'in', 'instanceof', 'new', 'return', 'switch', 'this', 'throw', 'try',
                   'typeof', 'var', 'void', 'while', 'with')
_input_element = re.compile(r'\s*(?:%(comment)s|%(token)s|%(lop)s|%(uop)s|%(aop)s|%(op)s|%(rel)s|%(punct)s)\s*' % {
    'comment': COMMENT_RE,
    'token': TOKENS_RE,
    'lop': LOGICAL_OPERATORS_RE,
    'uop': UNARY_OPERATORS_RE,
    'aop': ASSIGN_OPERATORS_RE,
    'op': OPERATORS_RE,
    'rel': RELATIONS_RE,
    'punct': PUNCTUATIONS_RE
})


class TokenStream(object):
    def __init__(self, code, start=0):
        self.code = code
        self.ended = False
        self.peeked = []
        self._ts = self._next_token(start)
        self._last = None

    def _next_token(self, pos=0):
        while not self.ended:
            feed_m = _input_element.match(self.code, pos)
            if feed_m is not None:
                token_id = feed_m.lastgroup
                token_value = feed_m.group(token_id)
                pos = feed_m.start(token_id)
                self.ended = feed_m.end() >= len(self.code)  # because how yield works
                if token_id == 'comment':
                    pass
                # TODO date
                elif token_id == 'null':
                    yield (token_id, None, pos)
                elif token_id == 'bool':
                    yield (token_id, {'true': True, 'false': False}[token_value], pos)
                elif token_id == 'str':
                    yield (token_id, token_value, pos)
                elif token_id == 'int':
                    yield (token_id, int(token_value), pos)
                elif token_id == 'float':
                    yield (token_id, float(token_value), pos)
                elif token_id == 'regex':
                    # TODO error handling
                    regex = re.compile(feed_m.group('rebody'))
                    yield (token_id, (regex, feed_m.group('reflags')), pos)
                elif token_id == 'id':
                    yield (token_id, token_value, pos)
                elif token_id in _operator_lookup:
                    yield (token_id, _operator_lookup[token_id][token_value], pos)
                elif token_id == 'punc':
                    yield (_PUNCTUATIONS[token_value], token_value, pos)
                else:
                    raise ExtractorError('Unexpected token at %d' % pos)
                pos = feed_m.end()
            else:
                raise ExtractorError('Unrecognised sequence at %d' % pos)
        raise StopIteration

    def chk_id(self, last=False):
        if last:
            name, value, pos = self._last
        else:
            name, value, pos = self.peek()
        if name != 'id' or value in _reserved_words:
            raise ExtractorError('Invalid identifier at %d' % pos)

    def peek(self, count=1):
        for _ in range(count - len(self.peeked)):
            token = next(self._ts, None)
            if token is None:
                self.peeked.append(('end', ';', len(self.code)))
            else:
                self.peeked.append(token)
        return self.peeked[count - 1]

    def pop(self):
        if not self.peeked:
            self.peek()
        self._last = self.peeked.pop(0)
        return self._last

    def last(self):
        return self._last
