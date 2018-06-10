from __future__ import unicode_literals

import re
import operator

from ..utils import ExtractorError
from .jsgrammar import (
    ASSIGN_OPERATORS_RE,
    COMMENT_RE,
    LINETERMINATORSEQ_RE,
    LOGICAL_OPERATORS_RE,
    OPERATORS_RE,
    TOKENS_RE,
    PUNCTUATIONS_RE,
    RELATIONS_RE,
    UNARY_OPERATORS_RE,
    TokenTypes
)

_PUNCTUATIONS = {
    '{': TokenTypes.COPEN,
    '}': TokenTypes.CCLOSE,
    '(': TokenTypes.POPEN,
    ')': TokenTypes.PCLOSE,
    '[': TokenTypes.SOPEN,
    ']': TokenTypes.SCLOSE,
    '.': TokenTypes.DOT,
    ';': TokenTypes.END,
    ',': TokenTypes.COMMA,
    '?': TokenTypes.HOOK,
    ':': TokenTypes.COLON
}
_LOGICAL_OPERATORS = {
    '&&': (TokenTypes.AND, lambda cur, right: cur and right),
    '||': (TokenTypes.OR, lambda cur, right: cur or right)
}
_UNARY_OPERATORS = {
    '+': (TokenTypes.PLUS, lambda cur: cur),
    '-': (TokenTypes.NEG, lambda cur: cur * -1),
    '++': (TokenTypes.INC, lambda cur: cur + 1),
    '--': (TokenTypes.DEC, lambda cur: cur - 1),
    '!': (TokenTypes.NOT, operator.not_),
    '~': (TokenTypes.BNOT, operator.inv),
    # XXX define these operators
    'delete': (TokenTypes.DEL, None),
    'void': (TokenTypes.VOID, None),
    'typeof': (TokenTypes.TYPE, lambda cur: type(cur))
}
_RELATIONS = {
    '<': (TokenTypes.LT, operator.lt),
    '>': (TokenTypes.GT, operator.gt),
    '<=': (TokenTypes.LE, operator.le),
    '>=': (TokenTypes.GE, operator.ge),
    # XXX check python and JavaScript equality difference
    '==': (TokenTypes.EQ, operator.eq),
    '!=': (TokenTypes.NE, operator.ne),
    '===': (TokenTypes.SEQ, lambda cur, right: cur == right and type(cur) == type(right)),
    '!==': (TokenTypes.SNE, lambda cur, right: not cur == right or not type(cur) == type(right)),
    'in': (TokenTypes.IN, operator.contains),
    'instanceof': (TokenTypes.INSTANCEOF, lambda cur, right: isinstance(cur, right))
}
_OPERATORS = {
    '|': (TokenTypes.BOR, operator.or_),
    '^': (TokenTypes.BXOR, operator.xor),
    '&': (TokenTypes.BAND, operator.and_),
    # NOTE convert to int before shift float
    '>>': (TokenTypes.RSHIFT, operator.rshift),
    '<<': (TokenTypes.LSHIFT, operator.lshift),
    '>>>': (TokenTypes.URSHIFT, lambda cur, right: cur >> right if cur >= 0 else (cur + 0x100000000) >> right),
    '-': (TokenTypes.SUB, operator.sub),
    '+': (TokenTypes.ADD, operator.add),
    '%': (TokenTypes.MOD, operator.mod),
    '/': (TokenTypes.DIV, operator.truediv),
    '*': (TokenTypes.MUL, operator.mul)
}
_ASSIGN_OPERATORS = dict((op + '=', ('set_%s' % token[0], token[1])) for op, token in _OPERATORS.items())
_ASSIGN_OPERATORS['='] = ('set', lambda cur, right: right)

_operator_lookup = {
    TokenTypes.OP: _OPERATORS,
    TokenTypes.AOP: _ASSIGN_OPERATORS,
    TokenTypes.UOP: _UNARY_OPERATORS,
    TokenTypes.LOP: _LOGICAL_OPERATORS,
    TokenTypes.REL: _RELATIONS
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

_line_terminator = re.compile(LINETERMINATORSEQ_RE)


def convert_to_unary(token_value):
    return {TokenTypes.ADD: _UNARY_OPERATORS['+'], TokenTypes.SUB: _UNARY_OPERATORS['-']}[token_value[0]]


class Token(object):
    def __init__(self, token_type, token_value, pos, line, at):
        super(Token, self).__init__()
        self.id = token_type
        self.value = token_value
        self.pos = pos
        self.line = line
        self.at = at


class TokenStream(object):
    def __init__(self, code, start=0):
        super(TokenStream, self).__init__()
        self.code = code
        self.ended = False
        self.peeked = []
        self._ts = self._next_token(start)
        self._last = None
        self._line = 1 + len(_line_terminator.findall(self.code[:start]))

    def _next_token(self, pos=0):
        while not self.ended:
            feed_m = _input_element.match(self.code, pos)
            if feed_m is not None:
                token_id = feed_m.lastgroup
                token_value = feed_m.group(token_id)
                pos = feed_m.start(token_id)
                token_id = TokenTypes[TokenTypes.index(token_id)]

                # TODO use line report insteadof position
                lt_count, lt_match = 0, None
                for lt_count, lt_match in enumerate(_line_terminator.finditer(token_value)): pass
                lt_last = pos if lt_match is None else pos + lt_match.start()
                at = pos - lt_last
                self._line += lt_count

                self.ended = feed_m.end() >= len(self.code)  # because how yield works
                if token_id is TokenTypes.COMMENT:
                    pass
                # TODO date
                elif token_id is TokenTypes.NULL:
                    yield Token(token_id, None, pos, self._line, at)
                elif token_id is TokenTypes.BOOL:
                    yield Token(token_id, {'true': True, 'false': False}[token_value], pos, self._line, at)
                elif token_id is TokenTypes.STR:
                    yield Token(token_id, token_value[1:-1], pos, self._line, at)
                elif token_id is TokenTypes.INT:
                    root = ((16 if len(token_value) > 2 and token_value[1] in 'xX' else 8)
                            if token_value.startswith('0') else 10)
                    yield Token(token_id, int(token_value, root), pos, self._line, at)
                elif token_id is TokenTypes.FLOAT:
                    yield Token(token_id, float(token_value), pos, self._line, at)
                elif token_id is TokenTypes.REGEX:
                    # TODO error handling
                    regex = re.compile(feed_m.group('rebody'))
                    yield Token(token_id, (regex, feed_m.group('reflags')), pos, self._line, at)
                elif token_id is TokenTypes.ID:
                    yield Token(token_id, token_value, pos, self._line, at)
                elif token_id in _operator_lookup:
                    yield Token(token_id if token_value != 'in' else TokenTypes.IN,
                                _operator_lookup[token_id][token_value],
                                pos, self._line, at)
                elif token_id is TokenTypes.PUNCT:
                    yield Token(_PUNCTUATIONS[token_value], token_value, pos, self._line, at)
                else:
                    raise ExtractorError('Unexpected token at %d' % pos)
                pos = feed_m.end()
            elif pos >= len(self.code):
                self.ended = True
            else:
                raise ExtractorError('Unrecognised sequence at %d' % pos)
        
    def chk_id(self, last=False):
        if last:
            token = self._last
        else:
            token = self.peek()
        if token.id is not TokenTypes.ID or token.value in _reserved_words:
            raise ExtractorError('Invalid identifier at %d' % token.pos)

    def peek(self, count=1):
        for _ in range(count - len(self.peeked)):
            token = next(self._ts, None)
            if token is None:
                pos = len(self.code)

                lt_count, lt_match = 0, None
                for lt_count, lt_match in enumerate(_line_terminator.finditer(self.code)): pass
                lt_last = pos if lt_match is None else pos + lt_match.start()
                at = pos - lt_last

                self.peeked.append(Token(TokenTypes.END, ';', pos, self._line, at))
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
