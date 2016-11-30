from __future__ import unicode_literals

import json
import operator
import re
from collections import OrderedDict

from .utils import (
    ExtractorError,
)

__DECIMAL_RE = r'(?:[1-9][0-9]*)|0'
__OCTAL_RE = r'0+[0-7]*'
__HEXADECIMAL_RE = r'0[xX][0-9a-fA-F]+'
__ESC_UNICODE_RE = r'u[0-9a-fA-F]{4}'
__ESC_HEX_RE = r'x[0-9a-fA-F]{2}'

_OPERATORS = [
    ('|', operator.or_),
    ('^', operator.xor),
    ('&', operator.and_),
    ('>>', operator.rshift),
    ('<<', operator.lshift),
    ('-', operator.sub),
    ('+', operator.add),
    ('%', operator.mod),
    ('/', operator.truediv),
    ('*', operator.mul)
]
_ASSIGN_OPERATORS = [(op + '=', opfunc) for op, opfunc in _OPERATORS]
_ASSIGN_OPERATORS.append(('=', lambda cur, right: right))

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

_TOKENS = OrderedDict([
    ('id', _NAME_RE),
    ('null', _NULL_RE),
    ('bool', _BOOL_RE),
    ('str', _STRING_RE),
    ('int', _INTEGER_RE),
    ('float', _FLOAT_RE),
    ('regex', _REGEX_RE)
])

_PUNCTUATIONS = {
    'copen': '{',
    'cclose': '}',
    'popen': '(',
    'pclose': ')',
    'sopen': '[',
    'sclose': ']',
    'dot': '.',
    'end': ';',
    'comma': ','
}

token_ids = dict((token[0], i) for i, token in enumerate(_TOKENS))
op_ids = dict((op[0], i) for i, op in _OPERATORS)
aop_ids = dict((aop[0], i)for i, aop in _ASSIGN_OPERATORS)

_COMMENT_RE = r'(?P<comment>/\*(?:(?!\*/)(?:\n|.))*\*/)'
_TOKENS_RE = r'|'.join('(?P<%(id)s>%(value)s)' % {'id': name, 'value': value}
                       for name, value in _TOKENS)
_RESERVED_WORDS_RE = r'(?:(?P<rsv>%s)\b)' % r'|'.join(_RESERVED_WORDS)
_PUNCTUATIONS_RE = r'|'.join(r'(?P<%(id)s>%(value)s)' % {'id': name, 'value': re.escape(value)}
                             for name, value in _PUNCTUATIONS.items())
_OPERATORS_RE = r'(?P<op>%s)' % r'|'.join(re.escape(op) for op, opfunc in _OPERATORS)
_ASSIGN_OPERATORS_RE = r'(?P<assign>%s)' % r'|'.join(re.escape(op) for op, opfunc in _ASSIGN_OPERATORS)

input_element = re.compile(r'''\s*(?:%(comment)s|%(rsv)s|%(token)s|%(punct)s|%(assign)s|%(op)s)\s*''' % {
    'comment': _COMMENT_RE,
    'rsv': _RESERVED_WORDS_RE,
    'token': _TOKENS_RE,
    'punct': _PUNCTUATIONS_RE,
    'assign': _ASSIGN_OPERATORS_RE,
    'op': _OPERATORS_RE
})


class JSInterpreter(object):
    def __init__(self, code, objects=None):
        if objects is None:
            objects = {}
        self.code = code
        self._functions = {}
        self._objects = objects

    @staticmethod
    def _next_statement(code, pos=0, stack_size=100):
        def next_statement(lookahead, stack_top=100):
            # TODO migrate interpretation
            statement = []
            feed_m = None
            while lookahead < len(code):
                feed_m = input_element.match(code, lookahead)
                if feed_m is not None:
                    token_id = feed_m.lastgroup
                    if token_id in ('pclose', 'sclose', 'cclose', 'comma', 'end'):
                        return statement, lookahead, feed_m.end()
                    token_value = feed_m.group(token_id)
                    lookahead = feed_m.end()
                    if token_id == 'comment':
                        pass
                    elif token_id == 'rsv':
                        statement.append((token_id, token_value))
                        if token_value == 'return':
                            expressions, lookahead, _ = next_statement(lookahead, stack_top - 1)
                            statement.extend(expressions)
                    elif token_id in ('id', 'op', 'dot'):
                        if token_id == 'id':
                            # TODO handle label
                            pass
                        statement.append((token_id, token_value))
                    elif token_id in token_ids:
                        # TODO date
                        # TODO error handling
                        if token_id == 'null':
                            statement.append((token_id, None))
                        elif token_id == 'bool':
                            statement.append((token_id, {'true': True, 'false': False}[token_value]))
                        elif token_id == 'str':
                            statement.append((token_id, token_value))
                        elif token_id == 'int':
                            statement.append((token_id, int(token_value)))
                        elif token_id == 'float':
                            statement.append((token_id, float(token_value)))
                        elif token_id == 'regex':
                            regex = re.compile(feed_m.group('rebody'))
                            statement.append((token_id, {'re': regex, 'flags': feed_m.group('reflags')}))
                    elif token_id in ('assign', 'popen', 'sopen'):
                        statement.append((token_id, token_value))
                        while lookahead < len(code):
                            expressions, lookahead, _ = next_statement(lookahead, stack_top - 1)
                            statement.extend(expressions)
                            peek = input_element.match(code, lookahead)
                            if peek is not None:
                                peek_id = peek.lastgroup
                                peek_value = peek.group(peek_id)
                                if ((token_id == 'popen' and peek_id == 'pclose') or
                                        (token_id == 'sopen' and peek_id == 'sclose')):
                                    statement.append((peek_id, peek_value))
                                    lookahead = peek.end()
                                    break
                                elif peek_id == 'comma':
                                    statement.append((peek_id, peek_value))
                                    lookahead = peek.end()
                                elif peek_id == 'end':
                                    break
                                else:
                                    raise ExtractorError('Unexpected character %s at %d' % (
                                        peek_value, peek.start(peek_id)))
                            else:
                                raise ExtractorError("Not yet implemented")
                else:
                    raise ExtractorError("Not yet implemented")
            return statement, lookahead, lookahead if feed_m is None else feed_m.end()

        while pos < len(code):
            stmt, _, pos = next_statement(pos, stack_size)
            # XXX backward compatibility till parser migration
            yield ''.join(str(value) for _, value in stmt)
        raise StopIteration

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
            for stmt in self._next_statement(code):
                res, abort = self.interpret_statement(stmt, local_vars)
                if abort:
                    break
            return res
        return resf
