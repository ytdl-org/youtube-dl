from __future__ import unicode_literals

import json
import operator
import re

from .utils import (
    ExtractorError,
)

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
_UNARY_OPERATORS ={
    '++': ('inc', lambda cur: cur + 1),
    '--': ('dec', lambda cur: cur - 1),
    '!': ('not', operator.not_),
    '~': ('bnot', lambda cur: cur ^ -1)
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
_bitwise_operator_order = ['|', '^', '&']
_operator_order = ['>>>', '>>', '<<', '-', '+', '%', '/', '*']
_assign_operator_order = ['=']
_assign_operator_order.extend(op + '=' for op in _bitwise_operator_order)
_assign_operator_order.extend(op + '=' for op in _operator_order)

# TODO flow control and others probably
_RESERVED_WORDS = ['function', 'var', 'const', 'return']

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
# _RESERVED_WORDS_RE = r'(?:(?P<rsv>%s)\b)' % r'|'.join(_RESERVED_WORDS)
_PUNCTUATIONS_RE = r'|'.join(r'(?P<%(id)s>%(value)s)' % {'id': name, 'value': re.escape(value)}
                             for name, value in _PUNCTUATIONS.items())
_LOGICAL_OPERATORS_RE = r'(?P<lop>%s)' % r'|'.join(re.escape(value) for value in _logical_operator_order)
_UNARY_OPERATORS_RE = r'(?P<uop>%s)' % r'|'.join(re.escape(value) for value in _unary_operator_order)
_RELATIONS_RE = r'(?P<rel>%s)' % r'|'.join(re.escape(value) for value in _relation_order)
_OPERATORS_RE = r'(?P<op>%s)' % r'|'.join(re.escape(value) for value in _operator_order)
_ASSIGN_OPERATORS_RE = r'(?P<assign>%s)' % r'|'.join(re.escape(value) for value in _assign_operator_order)

input_element = re.compile(r'\s*(?:%(comment)s|%(token)s|%(punct)s|%(lop)s|%(uop)s|%(rel)s|%(assign)s|%(op)s)\s*' % {
    'comment': _COMMENT_RE,
    'token': _TOKENS_RE,
    'punct': _PUNCTUATIONS_RE,
    'lop': _LOGICAL_OPERATORS_RE,
    'uop': _UNARY_OPERATORS_RE,
    'rel': _RELATIONS_RE,
    'assign': _ASSIGN_OPERATORS_RE,
    'op': _OPERATORS_RE
})


class TokenStream(object):
    def __init__(self, code, start=0):
        self.code = code
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
            self.peeked.append(next(self._ts, ('end', ';', len(self.code))))
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
        # TODO migrate interpretation
        # ast
        statement = []
        while True:
            token_id, token_value, token_pos = token_stream.peek()
            if token_id in ('pclose', 'sclose', 'cclose', 'comma', 'end'):
                # empty statement goes straight here
                return statement, False
            token_stream.pop()
            if token_id == 'id' and token_value == 'function':
                # TODO handle funcdecl
                pass
            elif token_id == 'copen':
                # block
                statement_list = []
                for s in self._next_statement(token_stream, stack_top - 1):
                    statement_list.append(s)
                    token_id, token_value, token_pos = token_stream.peek()
                    if token_id == 'cclose':
                        token_stream.pop()
                        break
                statement.append(('block', statement_list))
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
                            init.append(self._assign_expression(token_stream))
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
                    statement.append(('vardecl', self._expression(token_stream)))

                elif (token_value in ('new', 'this', 'function') or
                              token_id in ('id', 'str', 'int', 'float', 'array', 'object', 'popen')):
                    # TODO conditional_expr ->> lhs_expr
                    # TODO func_expr
                    # lhs_expr -> new_expr | call_expr
                    # call_expr -> member_expr args | call_expr args | call_expr [ expr ] | call_expr . id_name
                    # new_expr -> member_expr | new member_expr
                    # member_expr -> prime_expr | func_expr |
                    #                member_expr [ expr ] |  member_expr . id_name | new member_expr args
                    # prime_expr -> 'this' | id | literal | array | object | '(' expr ')'
                    pass
                elif token_value == 'if':
                    pass
                elif token_value in ('for', 'do', 'while'):
                    pass
                elif token_value in ('break', 'continue'):
                    pass
                elif token_value == 'return':
                    pass
                elif token_value == 'with':
                    pass
                elif token_value == 'switch':
                    pass
                elif token_value == 'throw':
                    pass
                elif token_value == 'try':
                    pass
                elif token_value == 'debugger':
                    pass
            elif token_id in ('assign', 'popen', 'sopen', 'copen'):
                # TODO handle prop_name in object literals
                statement.append((token_id, token_value))
                while True:
                    expressions, _ = self._next_statement(token_stream, stack_top - 1)
                    statement.extend(expressions)
                    peek_id, peek_value, peek_pos = token_stream.peek()
                    if ((token_id == 'popen' and peek_id == 'pclose') or
                            (token_id == 'sopen' and peek_id == 'sclose') or
                            (token_id == 'copen' and peek_id == 'cclose')):
                        statement.append((peek_id, peek_value))
                        token_stream.pop()
                        break
                    elif peek_id == 'comma':
                        statement.append((peek_id, peek_value))
                        token_stream.pop()
                    elif peek_id == 'end':
                        break
                    else:
                        # FIXME automatic end insertion
                        # TODO detect unmatched parentheses
                        raise ExtractorError('Unexpected sequence %s at %d' % (
                            peek_value, peek_pos))
            else:
                statement.append((token_id, token_value))
        return statement, True

    def statements(self, code=None, pos=0, stack_size=100):
        if code is None:
            code = self.code
        ts = TokenStream(code, pos)
        ended = False

        while not ended:
            stmt, ended = self._next_statement(ts, stack_size)
            yield stmt
            ts.pop()
        raise StopIteration

    def _expression(self, token_stream):
        # TODO expression
        pass

    def _assign_expression(self, token_stream):
        left = self._lefthand_side_expression(token_stream)
        peek_id, peek_value, peek_pos = token_stream.peek()
        if peek_id in _assign_operator_order:
            pass
        elif peek_id == 'hook':
            pass
        elif peek_id in _logical_operator_order:
            pass
        elif peek_id in _bitwise_operator_order:
            pass
        elif peek_id in _relation_order:
            pass
        elif peek_id in _operator_order:
            pass
        elif peek_id in _unary_operator_order:
            pass
        else:
            return ('assign', left, None)
        token_stream.pop()

    def _lefthand_side_expression(self, token_stream):
        # TODO lefthand_side_expression
        pass

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