from __future__ import unicode_literals

import json
import operator
import re

from .utils import (
    ExtractorError,
)

__DECIMAL_RE = r'(?:[1-9][0-9]*)|0'
__OCTAL_RE = r'0+[0-7]+'
__HEXADECIMAL_RE = r'(0[xX])[0-9a-fA-F]+'

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

_RESERVED_RE = r'(?:function|var|(?P<ret>return))\s'

_OPERATORS_RE = r'|'.join(re.escape(op) for op, opfunc in _OPERATORS)
_ASSIGN_OPERATORS_RE = r'|'.join(re.escape(op) for op, opfunc in _ASSIGN_OPERATORS)

_NAME_RE = r'[a-zA-Z_$][a-zA-Z_$0-9]*'

_SINGLE_QUOTED = r"""'(?:[^'\\\\]*(?:\\\\\\\\|\\\\['"nurtbfx/\\n]))*[^'\\\\]*'"""
_DOUBLE_QUOTED = r'''"(?:[^"\\\\]*(?:\\\\\\\\|\\\\['"nurtbfx/\\n]))*[^"\\\\]*"'''
_STRING_RE = r'%s|%s' % (_SINGLE_QUOTED, _DOUBLE_QUOTED)

_INTEGER_RE = r'%(hex)s|%(dec)s|%(oct)s' % {'hex': __HEXADECIMAL_RE, 'dec': __DECIMAL_RE, 'oct': __OCTAL_RE}
_FLOAT_RE = r'(%(dec)s)?\.%(dec)s' % {'dec': __DECIMAL_RE}

_BOOL_RE = r'true|false'
# XXX: it seams group cannot be refed this way
# r'/(?=[^*])[^/\n]*/(?![gimy]*(?P<reflag>[gimy])[gimy]*\g<reflag>)[gimy]{0,4}'
_REGEX_RE = r'''/(?=[^*])
    ((\\([tnvfr0.\\+*?^$\[\]{}()|/]|[0-7]{3}|x[0-9A-Fa-f]{2}|u[0-9A-Fa-f]{4}|c[A-Z]|))|
    [^/\n])*/[gimy]{0,4}'''

_LITERAL_RE = r'((?P<int>%(int)s)|(?P<float>%(float)s)|(?P<str>%(str)s)|(?P<bool>%(bool)s)|(?P<regex>%(regex)s))' % {
    'int': _INTEGER_RE,
    'float': _FLOAT_RE,
    'str': _STRING_RE,
    'bool': _BOOL_RE,
    'regex': _REGEX_RE
}

# _ARRAY_RE = r'\[(%(literal)s\s*,\s*)*(%(literal)s\s*)?\]' % {'literal': _LITERAL_RE}
# _VALUE_RE = r'(?:%(literal)s)|(%(array)s)' % {'literal': _LITERAL_RE, 'array': _ARRAY_RE}
_CALL_RE = r'\.?(%(name)s)?\s*\(' % {'name': _NAME_RE}  # function or method!

_COMMENT_RE = r'/\*(?:(?!\*/)(?:\n|.))*\*/'

token = re.compile(r'''(?x)\s*(?:
    (?P<comment>%(comment)s)|(?P<rsv>%(rsv)s)|
    (?P<call>%(call)s)|(?P<elem>%(name)s\s*\[)|
    (?P<id>%(name)s)|(?P<field>\.%(name)s)|
    (?P<val>%(val)s)|(?P<assign>%(aop)s)|(?P<op>%(op)s)|
    (?P<popen>\()|(?P<array>\[)|(?P<pclose>\))|(?P<sclose>\])|
    (?P<expend>,)|(?P<end>;)
    )\s*''' % {
    'comment': _COMMENT_RE,
    'rsv': _RESERVED_RE,
    'call': _CALL_RE,
    'name': _NAME_RE,
    'val': _LITERAL_RE,
    'aop': _ASSIGN_OPERATORS_RE,
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
    def _next_statement(code, pos=0):
        def parse_expression(_pos, allowrecursion=100):
            expr = ''
            while _pos < len(code):
                feed_m = token.match(code[_pos:])
                if feed_m:
                    token_id = feed_m.lastgroup
                    if token_id in ('pclose', 'sclose', 'expend', 'end'):
                        return _pos, expr, feed_m.end()
                    _pos += feed_m.end()
                    if token_id == 'comment':
                        pass
                    elif token_id == 'rsv':
                        expr += feed_m.group(token_id)
                        if feed_m.group('ret') is not None:
                            _pos, parsed_expr, _ = parse_expression(_pos, allowrecursion - 1)
                            expr += parsed_expr
                    elif token_id in ('id', 'field', 'val', 'op'):
                        expr += feed_m.group(token_id)
                    elif token_id in ('assign', 'call', 'elem', 'popen', 'array'):
                        expr += feed_m.group(token_id)
                        while _pos < len(code):
                            _pos, parsed_expr, _ = parse_expression(_pos, allowrecursion - 1)
                            expr += parsed_expr
                            peek = token.match(code[_pos:])
                            if peek:
                                peek_id = peek.lastgroup
                                if (token_id == 'call' and peek_id == 'pclose' or
                                        token_id == 'elem' and peek_id == 'sclose' or
                                        token_id == 'popen' and peek_id == 'pclose' or
                                        token_id == 'array' and peek_id == 'sclose'):
                                    expr += peek.group(peek_id)
                                    _pos += peek.end()
                                    break
                                elif peek_id == 'end':
                                    break
                                elif peek_id == 'expend':
                                    expr += peek.group(peek_id)
                                    _pos += peek.end()
                                else:
                                    raise ExtractorError('Unexpected character %s at %d' % (
                                        peek.group(peek_id), _pos + peek.start(peek_id)))
                            else:
                                raise ExtractorError("Not yet implemented")
                else:
                    raise ExtractorError("Not yet implemented")
            raise ExtractorError('Runaway script')

        while pos < len(code):
            pos, stmt, lookahead = parse_expression(pos)
            pos += lookahead
            yield stmt
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
