from __future__ import unicode_literals

import json
import operator
import re

from .utils import ExtractorError

__DECIMAL_RE = r'(?:[1-9][0-9]*)|0'
__OCTAL_RE = r'0[0-7]+'
__HEXADECIMAL_RE = r'0[xX][0-9a-fA-F]+'
__ESC_UNICODE_RE = r'u[0-9a-fA-F]{4}'
__ESC_HEX_RE = r'x[0-9a-fA-F]{2}'

_PUNCTUATIONS = {
    'copen': '{',
    'cclose': '}',
    'popen': '(',
    'pclose': ')',
    'sopen': '[',
    'sclose': ']',
    'dot': '.',
    'end': ';',
    'comma': ',',
    'hook': '?',
    'colon': ':'
}

# TODO find a final storage solution (already)
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

# NOTE merely fixed due to regex matching, does not represent any precedence
_logical_operator_order = _LOGICAL_OPERATORS.keys()  # whatever
_unary_operator_order = _UNARY_OPERATORS.keys()  # evs
_relation_order = ['===', '!==', '==', '!=', '<=', '>=', '<', '>']
_operator_order = ['|', '^', '&', '>>>', '>>', '<<', '-', '+', '%', '/', '*']
_assign_operator_order = [op + '=' for op in _operator_order]
_assign_operator_order.append('=')

# only to check ids
_RESERVED_WORDS = ('break', 'case', 'catch', 'continue', 'debugger', 'default', 'delete', 'do', 'else', 'finally',
                   'for', 'function', 'if', 'in', 'instanceof', 'new', 'return', 'switch', 'this', 'throw',
                   'try', 'typeof', 'var', 'void', 'while', 'with')

# XXX add support for unicode chars
_NAME_RE = r'[a-zA-Z_$][a-zA-Z_$0-9]*'

# non-escape char also can be escaped, but line continuation and quotes has to be
# XXX unicode and hexadecimal escape sequences should be validated
_SINGLE_QUOTED_RE = r"""'(?:(?:\\'|\n)|[^'\n])*'"""
_DOUBLE_QUOTED_RE = r'''"(?:(?:\\"|\n)|[^"\n])*"'''
_STRING_RE = r'(?:%s)|(?:%s)' % (_SINGLE_QUOTED_RE, _DOUBLE_QUOTED_RE)

_INTEGER_RE = r'(?:%(hex)s)|(?:%(dec)s)|(?:%(oct)s)' % {'hex': __HEXADECIMAL_RE, 'dec': __DECIMAL_RE, 'oct': __OCTAL_RE}
_FLOAT_RE = r'(?:(?:%(dec)s\.[0-9]*)|(?:\.[0-9]+))(?:[eE][+-]?[0-9]+)?' % {'dec': __DECIMAL_RE}

_BOOL_RE = r'true|false'
_NULL_RE = r'null'

# XXX early validation might needed
# r'''/(?!\*)
#     (?:(?:\\(?:[tnvfr0.\\+*?^$\[\]{}()|/]|[0-7]{3}|x[0-9A-Fa-f]{2}|u[0-9A-Fa-f]{4}|c[A-Z]|))|[^/\n])*
#     /(?:(?![gimy]*(?P<flag>[gimy])[gimy]*(?P=flag))[gimy]{0,4}\b|\s|$)'''
_REGEX_FLAGS_RE = r'(?![gimy]*(?P<reflag>[gimy])[gimy]*(?P=reflag))(?P<reflags>[gimy]{0,4}\b)'
_REGEX_RE = r'/(?!\*)(?P<rebody>(?:[^/\n]|(?:\\/))*)/(?:(?:%s)|(?:\s|$))' % _REGEX_FLAGS_RE

re.compile(_REGEX_RE)

_TOKENS = [
    ('null', _NULL_RE),
    ('bool', _BOOL_RE),
    ('id', _NAME_RE),
    ('str', _STRING_RE),
    ('int', _INTEGER_RE),
    ('float', _FLOAT_RE),
    ('regex', _REGEX_RE)
]

_token_keys = set(name for name, value in _TOKENS)

_COMMENT_RE = r'(?P<comment>/\*(?:(?!\*/)(?:\n|.))*\*/)'
_TOKENS_RE = r'|'.join('(?P<%(id)s>%(value)s)' % {'id': name, 'value': value}
                       for name, value in _TOKENS)
_PUNCTUATIONS_RE = r'|'.join(r'(?P<%(id)s>%(value)s)' % {'id': name, 'value': re.escape(value)}
                             for name, value in _PUNCTUATIONS.items())
_LOGICAL_OPERATORS_RE = r'(?P<lop>%s)' % r'|'.join(re.escape(value) for value in _logical_operator_order)
_UNARY_OPERATORS_RE = r'(?P<uop>%s)' % r'|'.join(re.escape(value) for value in _unary_operator_order)
_RELATIONS_RE = r'(?P<rel>%s)' % r'|'.join(re.escape(value) for value in _relation_order)
_OPERATORS_RE = r'(?P<op>%s)' % r'|'.join(re.escape(value) for value in _operator_order)
_ASSIGN_OPERATORS_RE = r'(?P<aop>%s)' % r'|'.join(re.escape(value) for value in _assign_operator_order)

input_element = re.compile(r'\s*(?:%(comment)s|%(token)s|%(punct)s|%(lop)s|%(uop)s|%(rel)s|%(aop)s|%(op)s)\s*' % {
    'comment': _COMMENT_RE,
    'token': _TOKENS_RE,
    'punct': _PUNCTUATIONS_RE,
    'lop': _LOGICAL_OPERATORS_RE,
    'uop': _UNARY_OPERATORS_RE,
    'rel': _RELATIONS_RE,
    'aop': _ASSIGN_OPERATORS_RE,
    'op': _OPERATORS_RE
})


class TokenStream(object):
    def __init__(self, code, start=0):
        self.code = code
        self.ended = False
        self.peeked = []
        self._ts = self._next_token(start)

    def _next_token(self, pos=0):
        while pos < len(self.code):
            feed_m = input_element.match(self.code, pos)
            if feed_m is not None:
                token_id = feed_m.lastgroup
                token_value = feed_m.group(token_id)
                pos = feed_m.start(token_id)
                if token_id == 'comment':
                    pass
                elif token_id in _token_keys:
                    # TODO date
                    if token_id == 'null':
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
                        yield (token_id, {'re': regex, 'flags': feed_m.group('reflags')}, pos)
                    elif token_id in ('lor', 'uop', 'rel', 'aop', 'op'):
                        yield (token_id, _LOGICAL_OPERATORS[token_value])
                    else:
                        yield (token_id, token_value, pos)
                else:
                    yield (token_id, token_value, pos)
                pos = feed_m.end()
            else:
                raise ExtractorError('Unexpected character sequence at %d' % pos)
        raise StopIteration

    def peek(self, count=1):
        for _ in range(count - len(self.peeked)):
            token = next(self._ts, None)
            if token is None:
                self.ended = True
                self.peeked.append(('end', ';', len(self.code)))
            else:
                self.peeked.append(token)
        return self.peeked[count - 1]

    def pop(self):
        if not self.peeked:
            self.peek()
        return self.peeked.pop(0)


class JSInterpreter(object):
    undefined = object()

    def __init__(self, code, objects=None):
        if objects is None:
            objects = {}
        self.code = code
        self._functions = {}
        self._objects = objects

    @staticmethod
    def _chk_id(name, at):
        if name in _RESERVED_WORDS:
            raise ExtractorError('Invalid identifier at %d' % at)

    def _next_statement(self, token_stream, stack_top):
        if stack_top < 0:
            raise ExtractorError('Recursion limit reached')
        # TODO migrate interpretation
        # ast
        statement = None

        token_id, token_value, token_pos = token_stream.peek()
        if token_id in ('pclose', 'sclose', 'cclose', 'comma', 'end'):
            # empty statement goes straight here
            return statement
        token_stream.pop()
        if token_id == 'id' and token_value == 'function':
            # TODO handle funcdecl
            raise ExtractorError('Function declaration is not yet supported at %d' % token_pos)
        elif token_id == 'copen':
            # block
            token_stream.pop()
            statement_list = []
            for s in self._next_statement(token_stream, stack_top - 1):
                statement_list.append(s)
                token_id, token_value, token_pos = token_stream.peek()
                if token_id == 'cclose':
                    token_stream.pop()
                    break
            statement = ('block', statement_list)
        elif token_id == 'id':
            # TODO handle label
            if token_value == 'var':
                variables = []
                init = []
                has_another = True
                while has_another:
                    token_id, token_value, token_pos = token_stream.pop()
                    if token_id != 'id':
                        raise ExtractorError('Missing variable name at %d' % token_pos)
                    self._chk_id(token_value, token_pos)
                    variables.append(token_value)

                    peek_id, peek_value, peek_pos = token_stream.peek()
                    if peek_id == 'assign':
                        token_stream.pop()
                        init.append(self._assign_expression(token_stream, stack_top - 1))
                        peek_id, peek_value, peek_pos = token_stream.peek()
                    else:
                        init.append(JSInterpreter.undefined)

                    if peek_id == 'end':
                        has_another = False
                    elif peek_id == 'comma':
                        pass
                    else:
                        # FIXME automatic end insertion
                        # - token_id == cclose
                        # - check line terminator
                        # - restricted token
                        raise ExtractorError('Unexpected sequence %s at %d' % (peek_value, peek_pos))
                statement = ('vardecl', zip(variables, init))
            elif token_value == 'if':
                # TODO ifstatement
                raise ExtractorError('Conditional statement is not yet supported at %d' % token_pos)
            elif token_value in ('for', 'do', 'while'):
                # TODO iterstatement
                raise ExtractorError('Loops is not yet supported at %d' % token_pos)
            elif token_value in ('break', 'continue'):
                raise ExtractorError('Flow control is not yet supported at %d' % token_pos)
            elif token_value == 'return':
                token_stream.pop()
                statement = ('return', self._expression(token_stream, stack_top - 1))
                peek_id, peek_value, peek_pos = token_stream.peek()
                if peek_id != 'end':
                    # FIXME automatic end insertion
                    raise ExtractorError('Unexpected sequence %s at %d' % (peek_value, peek_pos))
            elif token_value == 'with':
                # TODO withstatement
                raise ExtractorError('With statement is not yet supported at %d' % token_pos)
            elif token_value == 'switch':
                # TODO switchstatement
                raise ExtractorError('Switch statement is not yet supported at %d' % token_pos)
            elif token_value == 'throw':
                # TODO throwstatement
                raise ExtractorError('Throw statement is not yet supported at %d' % token_pos)
            elif token_value == 'try':
                # TODO trystatement
                raise ExtractorError('Try statement is not yet supported at %d' % token_pos)
            elif token_value == 'debugger':
                # TODO debuggerstatement
                raise ExtractorError('Debugger statement is not yet supported at %d' % token_pos)
        # expr
        if statement is None:
            expr_list = []
            has_another = True
            while has_another:
                peek_id, peek_value, peek_pos = token_stream.peek()
                if not (peek_id == 'copen' and peek_id == 'id' and peek_value == 'function'):
                    expr_list.append(self._assign_expression(token_stream, stack_top - 1))
                    peek_id, peek_value, peek_pos = token_stream.peek()
                if peek_id == 'end':
                    has_another = False
                elif peek_id == 'comma':
                    pass
                else:
                    # FIXME automatic end insertion
                    raise ExtractorError('Unexpected sequence %s at %d' % (peek_value, peek_pos))

            statement = ('expr', expr_list)
        return statement

    def statements(self, code=None, pos=0, stack_size=100):
        if code is None:
            code = self.code
        ts = TokenStream(code, pos)

        while not ts.ended:
            yield self._next_statement(ts, stack_size)
            ts.pop()
        raise StopIteration

    def _expression(self, token_stream, stack_top):
        exprs = []
        has_another = True
        while has_another:
            exprs.append(self._assign_expression(token_stream, stack_top - 1))
            peek_id, peek_value, peek_pos = token_stream.peek()
            if peek_id == 'comma':
                token_stream.pop()
            elif peek_id == 'id' and peek_value == 'yield':
                # TODO yield
                raise ExtractorError('Yield statement is not yet supported at %d' % peek_pos)
            else:
                has_another = False
        return ('expr', exprs)

    def _assign_expression(self, token_stream, stack_top):
        # TODO track stack depth/height
        if stack_top < 0:
            raise ExtractorError('Recursion limit reached')

        left = self._conditional_expression(token_stream, stack_top - 1)
        peek_id, peek_value, peek_pos = token_stream.peek()
        if peek_id in _assign_operator_order:
            token_stream.pop()
            right = self._assign_expression(token_stream, stack_top - 1)
        else:
            right = None
        return ('assign', left, right)

    def _member_expression(self, token_stream, stack_top):
        peek_id, peek_value, peek_pos = token_stream.peek()
        if peek_id == 'id' and peek_value == 'new':
            token_stream.pop()
            target = self._member_expression(token_stream, stack_top - 1)
            args = self._arguments(token_stream, stack_top - 1)
            # Rhino has check for args length
            # Rhino has experimental syntax allowing an object literal to follow a new expression
        else:
            target = self._primary_expression(token_stream, stack_top)
            args = None

        return ('member', target, args, self._member_tail(token_stream, stack_top - 1))

    def _member_tail(self, token_stream, stack_top):
        peek_id, peek_value, peek_pos = token_stream.peek()
        if peek_id == 'dot':
            token_stream.pop()
            peek_id, peek_value, peek_pos = token_stream.peek()
            if peek_id == 'dot':
                token_stream.pop()
                peek_id, peek_value, peek_pos = token_stream.peek()
            elif peek_id == 'popen':
                # TODO handle field query
                raise ExtractorError('Field querry is not yet supported at %d' % peek_pos)

            if peek_id == 'id':
                token_stream.pop()
                return ('field', peek_value, self._member_tail(token_stream, stack_top - 1))
            else:
                raise ExtractorError('Identifier name expected at %d' % peek_pos)
        elif peek_id == 'sopen':
            token_stream.pop()
            index = self._expression(token_stream, stack_top - 1)
            token_id, token_value, token_pos = token_stream.pop()
            if token_id == 'sclose':
                return ('element', index, self._member_tail(token_stream, stack_top - 1))
            else:
                raise ExtractorError('Unexpected sequence at %d' % token_pos)
        elif peek_id == 'popen':
            args = self._arguments(token_stream, stack_top - 1)
            return ('call', args, self._member_tail(token_stream, stack_top - 1))
        else:
            return None

    def _primary_expression(self, token_stream, stack_top):
        # TODO support let
        peek_id, peek_value, peek_pos = token_stream.peek()
        if peek_id in _token_keys:
            token_stream.pop()
            if peek_id == 'id':
                # this
                if peek_value == 'this':
                    return ('rsv', 'this')
                # function expr
                elif peek_value == 'function':
                    # TODO function expression
                    raise ExtractorError('Function expression is not yet supported at %d' % peek_pos)
                # id
                else:
                    self._chk_id(peek_value, peek_pos)
                    return ('id', peek_value)
            # literals
            else:
                return (peek_id, peek_value)
        # array
        elif peek_id == 'sopen':
            return self._array_literal(token_stream, stack_top - 1)
        # object
        elif peek_id == 'copen':
            # TODO object
            raise ExtractorError('Object literals is not yet supported at %d' % peek_pos)
        # expr
        elif peek_id == 'popen':
            token_stream.pop()
            open_pos = peek_pos
            expr = self._expression(token_stream, stack_top - 1)
            peek_id, peek_value, peek_pos = token_stream.peek()
            if peek_id != 'pclose':
                raise ExtractorError('Unbalanced parentheses at %d' % open_pos)
            token_stream.pop()
            return ('expr', expr)
        # empty (probably)
        else:
            return None

    def _arguments(self, token_stream, stack_top):
        peek_id, peek_value, peek_pos = token_stream.peek()
        if peek_id == 'popen':
            token_stream.pop()
            open_pos = peek_pos
        else:
            return None
        args = []
        while True:
            peek_id, peek_value, peek_pos = token_stream.peek()
            if peek_id == 'pcolse':
                token_stream.pop()
                return args
            # FIXME handle infor
            args.append(self._assign_expression(token_stream, stack_top - 1))
            # TODO generator expression
            peek_id, peek_value, peek_pos = token_stream.peek()

            if peek_id not in ('comma', 'pclose'):
                raise ExtractorError('Unbalanced parentheses at %d' % open_pos)

    def _array_literal(self, token_stream, stack_top):
        # TODO check no line break
        peek_id, peek_value, peek_pos = token_stream.peek()
        if peek_pos != 'sopen':
            raise ExtractorError('Array expected at %d' % peek_pos)
        token_stream.pop()
        elements = []

        has_another = True
        while has_another:
            peek_id, peek_value, peek_pos = token_stream.peek()
            if peek_id == 'comma':
                token_stream.pop()
                elements.append(None)
            elif peek_id == 'sclose':
                token_stream.pop()
                has_another = False
            elif peek_id == 'id' and peek_value == 'for':
                # TODO array comprehension
                raise ExtractorError('Array comprehension is not yet supported at %d' % peek_pos)
            else:
                elements.append(self._assign_expression(token_stream, stack_top - 1))
                peek_id, peek_value, peek_pos = token_stream.pop()
                if peek_id != 'comma':
                    raise ExtractorError('Expected , after element at %d' % peek_pos)
        return ('array', elements)

    def _conditional_expression(self, token_stream, stack_top):
        expr = self._operator_expression(token_stream, stack_top - 1)
        peek_id, peek_value, peek_pos = token_stream.peek()
        if peek_id == 'hook':
            hook_pos = peek_pos
            true_expr = self._assign_expression(token_stream, stack_top - 1)
            peek_id, peek_value, peek_pos = token_stream.peek()
            if peek_id == 'colon':
                false_expr = self._assign_expression(token_stream, stack_top - 1)
            else:
                raise ExtractorError('Missing : in conditional expression at %d' % hook_pos)
            return ('cond', expr, true_expr, false_expr)
        return ('rpn', expr)

    def _operator_expression(self, token_stream, stack_top):
        #     --<---------------------------------<-- op --<--------------------------<----
        #     |                                                                           |
        #     |  --<-- prefix --<--                                  -->-- postfix -->--  |
        #     |  |                ^                                  ^                 |  ^
        #     v  v                |                                  |                 v  |
        # ->------------>----------->-- lefthand-side expression -->----------->------------>---|
        #
        # 20 grouping
        # ...  # handled by lefthandside_expression
        # 17 postfix
        # 16 unary
        # 15 exponentiation  # not yet found in grammar
        # 14 mul
        # 13 add
        # 12 shift
        # 11 rel
        # 10 eq
        # 9 band
        # 8 bxor
        # 7 bor
        # 6 land
        # 5 lor
        # 4 cond  # handled by conditional_expression

        out = []
        stack = []

        has_another = True
        while has_another:
            had_inc = False
            has_prefix = True
            while has_prefix:
                peek_id, peek_value, peek_pos = token_stream.peek()
                if peek_id == 'uop':
                    had_inc = peek_value in ('inc', 'dec')
                    while stack and stack[-1][0] < 16:
                        _, stack_op = stack.pop()
                        out.append(('op', stack_op))
                    _, op = peek_value
                    stack.append((16, op))
                    token_stream.pop()
                    peek_id, peek_value, peek_pos = token_stream.peek()
                    if had_inc and peek_id != 'id':
                        raise ExtractorError('Prefix operator has to be followed by an identifier at %d' % peek_pos)
                    has_prefix = peek_id == 'uop'
                else:
                    has_prefix = False

            left = self._member_expression(token_stream, stack_top - 1)
            out.append(left)

            peek_id, peek_value, peek_pos = token_stream.peek()
            # postfix
            if peek_id == 'uop':
                if had_inc:
                    raise ExtractorError('''Can't have prefix and postfix operator at the same time at %d''' % peek_pos)
                name, op = peek_value
                if name in ('inc', 'dec'):
                    prec = 17
                else:
                    raise ExtractorError('Unexpected operator at %d' % peek_pos)
                while stack and stack[-1][0] <= 17:
                    _, stack_op = stack.pop()
                    out.append(('op', stack_op))
                stack.append((prec, op))
                token_stream.pop()
                peek_id, peek_value, peek_pos = token_stream.peek()

            if peek_id == 'rel':
                name, op = peek_value
            elif peek_id == 'op':
                name, op = peek_value
                if name in ('mul', 'div', 'mod'):
                    prec = 14
                elif name in ('add', 'sub'):
                    prec = 13
                elif name.endswith('shift'):
                    prec = 12
                elif name == 'band':
                    prec = 9
                elif name == 'bxor':
                    prec = 8
                elif name == 'bor':
                    prec = 7
                else:
                    raise ExtractorError('Unexpected operator at %d' % peek_pos)
            elif peek_id == 'lop':
                name, op = peek_value
                prec = {'or': 5, 'and': 6}[name]
            else:
                has_another = False
                prec = 21  # empties stack

            while stack and stack[-1][0] <= prec:
                _, stack_op = stack.pop()
                out.append(('op', stack_op))
            if has_another:
                stack.append((prec, op))
                token_stream.pop()

        return ('rpn', out)

    def interpret_statement(self, stmt, local_vars, allow_recursion=100):
        if allow_recursion < 0:
            raise ExtractorError('Recursion limit reached')

        should_abort = False
        stmt = stmt.lstrip()
        stmt_m = re.match(r'var\s', stmt)
        if stmt_m:
            expr = stmt[len(stmt_m.group(0)):]
        else:
            return_m = re.match(r'return(?:\s+|$)', stmt)
            if return_m:
                expr = stmt[len(return_m.group(0)):]
                should_abort = True
            else:
                # Try interpreting it as an expression
                expr = stmt

        v = self.interpret_expression(expr, local_vars, allow_recursion)
        return v, should_abort

    def interpret_expression(self, expr, local_vars, allow_recursion):
        expr = expr.strip()

        if expr == '':  # Empty expression
            return None

        if expr.startswith('('):
            parens_count = 0
            for m in re.finditer(r'[()]', expr):
                if m.group(0) == '(':
                    parens_count += 1
                else:
                    parens_count -= 1
                    if parens_count == 0:
                        sub_expr = expr[1:m.start()]
                        sub_result = self.interpret_expression(
                            sub_expr, local_vars, allow_recursion)
                        remaining_expr = expr[m.end():].strip()
                        if not remaining_expr:
                            return sub_result
                        else:
                            expr = json.dumps(sub_result) + remaining_expr
                        break
            else:
                raise ExtractorError('Premature end of parens in %r' % expr)

        for op, opfunc in _ASSIGN_OPERATORS:
            m = re.match(r'''(?x)
                (?P<out>%s)(?:\[(?P<index>[^\]]+?)\])?
                \s*%s
                (?P<expr>.*)$''' % (_NAME_RE, re.escape(op)), expr)
            if not m:
                continue
            right_val = self.interpret_expression(
                m.group('expr'), local_vars, allow_recursion - 1)

            if m.groupdict().get('index'):
                lvar = local_vars[m.group('out')]
                idx = self.interpret_expression(
                    m.group('index'), local_vars, allow_recursion)
                assert isinstance(idx, int)
                cur = lvar[idx]
                val = opfunc(cur, right_val)
                lvar[idx] = val
                return val
            else:
                cur = local_vars.get(m.group('out'))
                val = opfunc(cur, right_val)
                local_vars[m.group('out')] = val
                return val

        if expr.isdigit():
            return int(expr)

        var_m = re.match(
            r'(?!if|return|true|false)(?P<name>%s)$' % _NAME_RE,
            expr)
        if var_m:
            return local_vars[var_m.group('name')]

        try:
            return json.loads(expr)
        except ValueError:
            pass

        m = re.match(
            r'(?P<var>%s)\.(?P<member>[^(]+)(?:\(+(?P<args>[^()]*)\))?$' % _NAME_RE,
            expr)
        if m:
            variable = m.group('var')
            member = m.group('member')
            arg_str = m.group('args')

            if variable in local_vars:
                obj = local_vars[variable]
            else:
                if variable not in self._objects:
                    self._objects[variable] = self.extract_object(variable)
                obj = self._objects[variable]

            if arg_str is None:
                # Member access
                if member == 'length':
                    return len(obj)
                return obj[member]

            assert expr.endswith(')')
            # Function call
            if arg_str == '':
                argvals = tuple()
            else:
                argvals = tuple([
                    self.interpret_expression(v, local_vars, allow_recursion)
                    for v in arg_str.split(',')])

            if member == 'split':
                assert argvals == ('',)
                return list(obj)
            if member == 'join':
                assert len(argvals) == 1
                return argvals[0].join(obj)
            if member == 'reverse':
                assert len(argvals) == 0
                obj.reverse()
                return obj
            if member == 'slice':
                assert len(argvals) == 1
                return obj[argvals[0]:]
            if member == 'splice':
                assert isinstance(obj, list)
                index, howMany = argvals
                res = []
                for i in range(index, min(index + howMany, len(obj))):
                    res.append(obj.pop(index))
                return res

            return obj[member](argvals)

        m = re.match(
            r'(?P<in>%s)\[(?P<idx>.+)\]$' % _NAME_RE, expr)
        if m:
            val = local_vars[m.group('in')]
            idx = self.interpret_expression(
                m.group('idx'), local_vars, allow_recursion - 1)
            return val[idx]

        for op, opfunc in _OPERATORS:
            m = re.match(r'(?P<x>.+?)%s(?P<y>.+)' % re.escape(op), expr)
            if not m:
                continue
            x, abort = self.interpret_statement(
                m.group('x'), local_vars, allow_recursion - 1)
            if abort:
                raise ExtractorError(
                    'Premature left-side return of %s in %r' % (op, expr))
            y, abort = self.interpret_statement(
                m.group('y'), local_vars, allow_recursion - 1)
            if abort:
                raise ExtractorError(
                    'Premature right-side return of %s in %r' % (op, expr))
            return opfunc(x, y)

        m = re.match(
            r'^(?P<func>%s)\((?P<args>[a-zA-Z0-9_$,]*)\)$' % _NAME_RE, expr)
        if m:
            fname = m.group('func')
            argvals = tuple([
                int(v) if v.isdigit() else local_vars[v]
                for v in m.group('args').split(',')]) if len(m.group('args')) > 0 else tuple()
            if fname not in self._functions:
                self._functions[fname] = self.extract_function(fname)
            return self._functions[fname](argvals)

        raise ExtractorError('Unsupported JS expression %r' % expr)

    def extract_object(self, objname):
        obj = {}
        obj_m = re.search(
            (r'(?:var\s+)?%s\s*=\s*\{' % re.escape(objname)) +
            r'\s*(?P<fields>([a-zA-Z$0-9]+\s*:\s*function\(.*?\)\s*\{.*?\}(?:,\s*)?)*)' +
            r'\}\s*;',
            self.code)
        fields = obj_m.group('fields')
        # Currently, it only supports function definitions
        fields_m = re.finditer(
            r'(?P<key>[a-zA-Z$0-9]+)\s*:\s*function'
            r'\((?P<args>[a-z,]+)\){(?P<code>[^}]+)}',
            fields)
        for f in fields_m:
            argnames = f.group('args').split(',')
            obj[f.group('key')] = self.build_function(argnames, f.group('code'))

        return obj

    def extract_function(self, funcname):
        func_m = re.search(
            r'''(?x)
                (?:function\s+%s|[{;,]\s*%s\s*=\s*function|var\s+%s\s*=\s*function)\s*
                \((?P<args>[^)]*)\)\s*
                \{(?P<code>[^}]+)\}''' % (
                re.escape(funcname), re.escape(funcname), re.escape(funcname)),
            self.code)
        if func_m is None:
            raise ExtractorError('Could not find JS function %r' % funcname)
        argnames = func_m.group('args').split(',')

        return self.build_function(argnames, func_m.group('code'))

    def call_function(self, funcname, *args):
        f = self.extract_function(funcname)
        return f(args)

    def build_function(self, argnames, code):
        def resf(args):
            local_vars = dict(zip(argnames, args))
            for stmt in self.statements(code):
                res, abort = self.interpret_statement(stmt, local_vars)
                if abort:
                    break
            return res
        return resf
