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
    OPERATORS_RE,
    Token
)

_PUNCTUATIONS = {
    '{': Token.COPEN,
    '}': Token.CCLOSE,
    '(': Token.POPEN,
    ')': Token.PCLOSE,
    '[': Token.SOPEN,
    ']': Token.SCLOSE,
    '.': Token.DOT,
    ';': Token.END,
    ',': Token.COMMA,
    '?': Token.HOOK,
    ':': Token.COLON
}
_LOGICAL_OPERATORS = {
    '&&': (Token.AND, lambda cur, right: cur and right),
    '||': (Token.OR, lambda cur, right: cur or right)
}
_UNARY_OPERATORS = {
    '++': (Token.INC, lambda cur: cur + 1),
    '--': (Token.DEC, lambda cur: cur - 1),
    '!': (Token.NOT, operator.not_),
    '~': (Token.BNOT, lambda cur: cur ^ -1),
    # XXX define these operators
    'delete': (Token.DEL, None),
    'void': (Token.VOID, None),
    'typeof': (Token.TYPE, lambda cur: type(cur))
}
_RELATIONS = {
    '<': (Token.LT, operator.lt),
    '>': (Token.GT, operator.gt),
    '<=': (Token.LE, operator.le),
    '>=': (Token.GE, operator.ge),
    # XXX add instanceof and in operators
    # XXX check python and JavaScript equality difference
    '==': (Token.EQ, operator.eq),
    '!=': (Token.NE, operator.ne),
    '===': (Token.SEQ, lambda cur, right: cur == right and type(cur) == type(right)),
    '!==': (Token.SNE, lambda cur, right: not cur == right or not type(cur) == type(right))
}
_OPERATORS = {
    '|': (Token.BOR, operator.or_),
    '^': (Token.BXOR, operator.xor),
    '&': (Token.BAND, operator.and_),
    # NOTE convert to int before shift float
    '>>': (Token.RSHIFT, operator.rshift),
    '<<': (Token.LSHIFT, operator.lshift),
    '>>>': (Token.URSHIFT, lambda cur, right: cur >> right if cur >= 0 else (cur + 0x100000000) >> right),
    '-': (Token.SUB, operator.sub),
    '+': (Token.ADD, operator.add),
    '%': (Token.MOD, operator.mod),
    '/': (Token.DIV, operator.truediv),
    '*': (Token.MUL, operator.mul)
}
_ASSIGN_OPERATORS = dict((op + '=', ('set_%s' % token[0], token[1])) for op, token in _OPERATORS.items())
_ASSIGN_OPERATORS['='] = ('set', lambda cur, right: right)

_operator_lookup = {
    Token.OP: _OPERATORS,
    Token.AOP: _ASSIGN_OPERATORS,
    Token.UOP: _UNARY_OPERATORS,
    Token.LOP: _LOGICAL_OPERATORS,
    Token.REL: _RELATIONS
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
                token_id = Token[Token.index(token_id)]
                self.ended = feed_m.end() >= len(self.code)  # because how yield works
                if token_id is Token.COMMENT:
                    pass
                # TODO date
                elif token_id is Token.NULL:
                    yield (token_id, None, pos)
                elif token_id is Token.BOOL:
                    yield (token_id, {'true': True, 'false': False}[token_value], pos)
                elif token_id is Token.STR:
                    yield (token_id, token_value[1:-1], pos)
                elif token_id is Token.INT:
                    yield (token_id, int(token_value), pos)
                elif token_id is Token.FLOAT:
                    yield (token_id, float(token_value), pos)
                elif token_id is Token.REGEX:
                    # TODO error handling
                    regex = re.compile(feed_m.group('rebody'))
                    yield (token_id, (regex, feed_m.group('reflags')), pos)
                elif token_id is Token.ID:
                    yield (token_id, token_value, pos)
                elif token_id in _operator_lookup:
                    yield (token_id, _operator_lookup[token_id][token_value], pos)
                elif token_id is Token.PUNCT:
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
        if name is not Token.ID or value in _reserved_words:
            raise ExtractorError('Invalid identifier at %d' % pos)

    def peek(self, count=1):
        for _ in range(count - len(self.peeked)):
            token = next(self._ts, None)
            if token is None:
                self.peeked.append((Token.END, ';', len(self.code)))
            else:
                self.peeked.append(token)
        return self.peeked[count - 1]

    def pop(self, count=1):
        if count > len(self.peeked):
            self.peek(count)
            self.flush()
        else:
            self._last = self.peeked[count - 1]
            self.peeked = self.peeked[count:]
        return self._last

    def flush(self):
        if self.peeked:
            self._last = self.peeked[-1]
            self.peeked = []
        return self._last

    def last(self):
        return self._last
