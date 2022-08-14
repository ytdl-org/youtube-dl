from __future__ import unicode_literals

import itertools
import json
import math
import operator
import re

from .utils import (
    NO_DEFAULT,
    ExtractorError,
    js_to_json,
    remove_quotes,
    unified_timestamp,
)
from .compat import (
    compat_collections_chain_map as ChainMap,
    compat_itertools_zip_longest as zip_longest,
    compat_str,
)

_NAME_RE = r'[a-zA-Z_$][\w$]*'

# (op, definition) in order of binding priority, tightest first
# avoid dict to maintain order
# definition None => Defined in JSInterpreter._operator
_DOT_OPERATORS = (
    ('.', None),
    # TODO: ('?.', None),
)

_OPERATORS = (
    ('|', operator.or_),
    ('^', operator.xor),
    ('&', operator.and_),
    ('>>', operator.rshift),
    ('<<', operator.lshift),
    ('+', operator.add),
    ('-', operator.sub),
    ('*', operator.mul),
    ('/', operator.truediv),
    ('%', operator.mod),
)

_COMP_OPERATORS = (
    ('===', operator.is_),
    ('==', operator.eq),
    ('!==', operator.is_not),
    ('!=', operator.ne),
    ('<=', operator.le),
    ('>=', operator.ge),
    ('<', operator.lt),
    ('>', operator.gt),
)

_LOG_OPERATORS = (
    ('&', operator.and_),
    ('|', operator.or_),
    ('^', operator.xor),
)

_SC_OPERATORS = (
    ('?', None),
    ('||', None),
    ('&&', None),
    # TODO: ('??', None),
)

_OPERATOR_RE = '|'.join(map(lambda x: re.escape(x[0]), _OPERATORS + _LOG_OPERATORS))

_MATCHING_PARENS = dict(zip(*zip('()', '{}', '[]')))
_QUOTES = '\'"'


def _ternary(cndn, if_true=True, if_false=False):
    """Simulate JS's ternary operator (cndn?if_true:if_false)"""
    if cndn in (False, None, 0, ''):
        return if_false
    try:
        if math.isnan(cndn):  # NB: NaN cannot be checked by membership
            return if_false
    except TypeError:
        pass
    return if_true


class JS_Break(ExtractorError):
    def __init__(self):
        ExtractorError.__init__(self, 'Invalid break')


class JS_Continue(ExtractorError):
    def __init__(self):
        ExtractorError.__init__(self, 'Invalid continue')


class LocalNameSpace(ChainMap):
    def __setitem__(self, key, value):
        for scope in self.maps:
            if key in scope:
                scope[key] = value
                return
        self.maps[0][key] = value

    def __delitem__(self, key):
        raise NotImplementedError('Deleting is not supported')

    def __repr__(self):
        return 'LocalNameSpace%s' % (self.maps, )


class JSInterpreter(object):
    __named_object_counter = 0

    def __init__(self, code, objects=None):
        self.code, self._functions = code, {}
        self._objects = {} if objects is None else objects

    class Exception(ExtractorError):
        def __init__(self, msg, *args, **kwargs):
            expr = kwargs.pop('expr', None)
            if expr is not None:
                msg = '{0} in: {1!r}'.format(msg.rstrip(), expr[:100])
            super(JSInterpreter.Exception, self).__init__(msg, *args, **kwargs)

    def _named_object(self, namespace, obj):
        self.__named_object_counter += 1
        name = '__youtube_dl_jsinterp_obj%d' % (self.__named_object_counter, )
        namespace[name] = obj
        return name

    @staticmethod
    def _separate(expr, delim=',', max_split=None, skip_delims=None):
        if not expr:
            return
        counters = {k: 0 for k in _MATCHING_PARENS.values()}
        start, splits, pos, skipping, delim_len = 0, 0, 0, 0, len(delim) - 1
        in_quote, escaping = None, False
        for idx, char in enumerate(expr):
            if not in_quote:
                if char in _MATCHING_PARENS:
                    counters[_MATCHING_PARENS[char]] += 1
                elif char in counters:
                    counters[char] -= 1
            if not escaping:
                if char in _QUOTES and in_quote in (char, None):
                    in_quote = None if in_quote else char
                else:
                    escaping = in_quote and char == '\\'
            else:
                escaping = False

            if char != delim[pos] or any(counters.values()) or in_quote:
                pos = skipping = 0
                continue
            elif skipping > 0:
                skipping -= 1
                continue
            elif pos == 0 and skip_delims:
                here = expr[idx:]
                for s in skip_delims if isinstance(skip_delims, (list, tuple)) else [skip_delims]:
                    if here.startswith(s) and s:
                        skipping = len(s) - 1
                        break
                if skipping > 0:
                    continue
            if pos < delim_len:
                pos += 1
                continue
            yield expr[start: idx - delim_len]
            start, pos = idx + 1, 0
            splits += 1
            if max_split and splits >= max_split:
                break
        yield expr[start:]

    @classmethod
    def _separate_at_paren(cls, expr, delim):
        separated = list(cls._separate(expr, delim, 1))

        if len(separated) < 2:
            raise cls.Exception('No terminating paren {delim} in {expr}'.format(**locals()))
        return separated[0][1:].strip(), separated[1].strip()

    @staticmethod
    def _all_operators():
        return itertools.chain(
            _SC_OPERATORS, _LOG_OPERATORS, _COMP_OPERATORS, _OPERATORS)

    def _operator(self, op, left_val, right_expr, expr, local_vars, allow_recursion):
        if op in ('||', '&&'):
            if (op == '&&') ^ _ternary(left_val):
                return left_val  # short circuiting
        elif op == '?':
            right_expr = _ternary(left_val, *self._separate(right_expr, ':', 1))

        right_val = self.interpret_expression(right_expr, local_vars, allow_recursion)
        opfunc = op and next((v for k, v in self._all_operators() if k == op), None)
        if not opfunc:
            return right_val

        try:
            return opfunc(left_val, right_val)
        except Exception as e:
            raise self.Exception('Failed to evaluate {left_val!r} {op} {right_val!r}'.format(**locals()), expr, cause=e)

    def _index(self, obj, idx):
        if idx == 'length':
            return len(obj)
        try:
            return obj[int(idx)] if isinstance(obj, list) else obj[idx]
        except Exception as e:
            raise self.Exception('Cannot get index {idx}'.format(**locals()), expr=repr(obj), cause=e)

    def _dump(self, obj, namespace):
        try:
            return json.dumps(obj)
        except TypeError:
            return self._named_object(namespace, obj)

    def interpret_statement(self, stmt, local_vars, allow_recursion=100):
        if allow_recursion < 0:
            raise self.Exception('Recursion limit reached')
        allow_recursion -= 1

        should_return = False
        sub_statements = list(self._separate(stmt, ';')) or ['']
        expr = stmt = sub_statements.pop().strip()
        for sub_stmt in sub_statements:
            ret, should_return = self.interpret_statement(sub_stmt, local_vars, allow_recursion)
            if should_return:
                return ret, should_return

        m = re.match(r'(?P<var>(?:var|const|let)\s)|return(?:\s+|$)', stmt)
        if m:
            expr = stmt[len(m.group(0)):].strip()
            should_return = not m.group('var')
        if not expr:
            return None, should_return

        if expr[0] in _QUOTES:
            inner, outer = self._separate(expr, expr[0], 1)
            inner = json.loads(js_to_json(inner + expr[0]))  # , strict=True))
            if not outer:
                return inner, should_return
            expr = self._named_object(local_vars, inner) + outer

        if expr.startswith('new '):
            obj = expr[4:]
            if obj.startswith('Date('):
                left, right = self._separate_at_paren(obj[4:], ')')
                left = self.interpret_expression(left, local_vars, allow_recursion)
                expr = unified_timestamp(left, False)
                if not expr:
                    raise self.Exception('Failed to parse date {left!r}'.format(**locals()), expr=expr)
                expr = self._dump(int(expr * 1000), local_vars) + right
            else:
                raise self.Exception('Unsupported object {obj}'.format(**locals()), expr=expr)

        if expr.startswith('void '):
            left = self.interpret_expression(expr[5:], local_vars, allow_recursion)
            return None, should_return

        if expr.startswith('{'):
            inner, outer = self._separate_at_paren(expr, '}')
            inner, should_abort = self.interpret_statement(inner, local_vars, allow_recursion)
            if not outer or should_abort:
                return inner, should_abort or should_return
            else:
                expr = self._dump(inner, local_vars) + outer

        if expr.startswith('('):
            inner, outer = self._separate_at_paren(expr, ')')
            inner, should_abort = self.interpret_statement(inner, local_vars, allow_recursion)
            if not outer or should_abort:
                return inner, should_abort or should_return
            else:
                expr = self._dump(inner, local_vars) + outer

        if expr.startswith('['):
            inner, outer = self._separate_at_paren(expr, ']')
            name = self._named_object(local_vars, [
                self.interpret_expression(item, local_vars, allow_recursion)
                for item in self._separate(inner)])
            expr = name + outer

        m = re.match(r'(?P<try>try|finally)\s*|(?:(?P<catch>catch)|(?P<for>for)|(?P<switch>switch))\s*\(', expr)
        md = m.groupdict() if m else {}
        if md.get('try'):
            if expr[m.end()] == '{':
                try_expr, expr = self._separate_at_paren(expr[m.end():], '}')
            else:
                try_expr, expr = expr[m.end() - 1:], ''
            ret, should_abort = self.interpret_statement(try_expr, local_vars, allow_recursion)
            if should_abort:
                return ret, True
            ret, should_abort = self.interpret_statement(expr, local_vars, allow_recursion)
            return ret, should_abort or should_return

        elif md.get('catch'):
            # We ignore the catch block
            _, expr = self._separate_at_paren(expr, '}')
            ret, should_abort = self.interpret_statement(expr, local_vars, allow_recursion)
            return ret, should_abort or should_return

        elif md.get('for'):
            constructor, remaining = self._separate_at_paren(expr[m.end() - 1:], ')')
            if remaining.startswith('{'):
                body, expr = self._separate_at_paren(remaining, '}')
            else:
                switch_m = re.match(r'switch\s*\(', remaining)  # FIXME
                if switch_m:
                    switch_val, remaining = self._separate_at_paren(remaining[switch_m.end() - 1:], ')')
                    body, expr = self._separate_at_paren(remaining, '}')
                    body = 'switch(%s){%s}' % (switch_val, body)
                else:
                    body, expr = remaining, ''
            start, cndn, increment = self._separate(constructor, ';')
            self.interpret_expression(start, local_vars, allow_recursion)
            while True:
                if not _ternary(self.interpret_expression(cndn, local_vars, allow_recursion)):
                    break
                try:
                    ret, should_abort = self.interpret_statement(body, local_vars, allow_recursion)
                    if should_abort:
                        return ret, True
                except JS_Break:
                    break
                except JS_Continue:
                    pass
                self.interpret_expression(increment, local_vars, allow_recursion)
            ret, should_abort = self.interpret_statement(expr, local_vars, allow_recursion)
            return ret, should_abort or should_return

        elif md.get('switch'):
            switch_val, remaining = self._separate_at_paren(expr[m.end() - 1:], ')')
            switch_val = self.interpret_expression(switch_val, local_vars, allow_recursion)
            body, expr = self._separate_at_paren(remaining, '}')
            items = body.replace('default:', 'case default:').split('case ')[1:]
            for default in (False, True):
                matched = False
                for item in items:
                    case, stmt = (i.strip() for i in self._separate(item, ':', 1))
                    if default:
                        matched = matched or case == 'default'
                    elif not matched:
                        matched = (case != 'default'
                                   and switch_val == self.interpret_expression(case, local_vars, allow_recursion))
                    if not matched:
                        continue
                    try:
                        ret, should_abort = self.interpret_statement(stmt, local_vars, allow_recursion)
                        if should_abort:
                            return ret
                    except JS_Break:
                        break
                if matched:
                    break
            ret, should_abort = self.interpret_statement(expr, local_vars, allow_recursion)
            return ret, should_abort or should_return

        # Comma separated statements
        sub_expressions = list(self._separate(expr))
        if len(sub_expressions) > 1:
            for sub_expr in sub_expressions:
                ret, should_abort = self.interpret_statement(sub_expr, local_vars, allow_recursion)
                if should_abort:
                    return ret, True
            return ret, False

        for m in re.finditer(r'''(?x)
                (?P<pre_sign>\+\+|--)(?P<var1>{_NAME_RE})|
                (?P<var2>{_NAME_RE})(?P<post_sign>\+\+|--)'''.format(**globals()), expr):
            var = m.group('var1') or m.group('var2')
            start, end = m.span()
            sign = m.group('pre_sign') or m.group('post_sign')
            ret = local_vars[var]
            local_vars[var] += 1 if sign[0] == '+' else -1
            if m.group('pre_sign'):
                ret = local_vars[var]
            expr = expr[:start] + self._dump(ret, local_vars) + expr[end:]

        if not expr:
            return None, should_return

        m = re.match(r'''(?x)
            (?P<assign>
                (?P<out>{_NAME_RE})(?:\[(?P<index>[^\]]+?)\])?\s*
                (?P<op>{_OPERATOR_RE})?
                =(?P<expr>.*)$
            )|(?P<return>
                (?!if|return|true|false|null|undefined)(?P<name>{_NAME_RE})$
            )|(?P<indexing>
                (?P<in>{_NAME_RE})\[(?P<idx>.+)\]$
            )|(?P<attribute>
                (?P<var>{_NAME_RE})(?:\.(?P<member>[^(]+)|\[(?P<member2>[^\]]+)\])\s*
            )|(?P<function>
                (?P<fname>{_NAME_RE})\((?P<args>.*)\)$
            )'''.format(**globals()), expr)
        md = m.groupdict() if m else {}
        if md.get('assign'):
            left_val = local_vars.get(m.group('out'))

            if not m.group('index'):
                local_vars[m.group('out')] = self._operator(
                    m.group('op'), left_val, m.group('expr'), expr, local_vars, allow_recursion)
                return local_vars[m.group('out')], should_return
            elif left_val is None:
                raise self.Exception('Cannot index undefined variable ' + m.group('out'), expr=expr)

            idx = self.interpret_expression(m.group('index'), local_vars, allow_recursion)
            if not isinstance(idx, (int, float)):
                raise self.Exception('List index %s must be integer' % (idx, ), expr=expr)
            idx = int(idx)
            left_val[idx] = self._operator(
                m.group('op'), left_val[idx], m.group('expr'), expr, local_vars, allow_recursion)
            return left_val[idx], should_return

        elif expr.isdigit():
            return int(expr), should_return

        elif expr == 'break':
            raise JS_Break()
        elif expr == 'continue':
            raise JS_Continue()

        elif md.get('return'):
            return local_vars[m.group('name')], should_return

        try:
            ret = json.loads(js_to_json(expr))  # strict=True)
            if not md.get('attribute'):
                return ret, should_return
        except ValueError:
            pass

        if md.get('indexing'):
            val = local_vars[m.group('in')]
            idx = self.interpret_expression(m.group('idx'), local_vars, allow_recursion)
            return self._index(val, idx), should_return

        for op, _ in self._all_operators():
            # hackety: </> have higher priority than <</>>, but don't confuse them
            skip_delim = (op + op) if op in ('<', '>') else None
            separated = list(self._separate(expr, op, skip_delims=skip_delim))
            if len(separated) < 2:
                continue

            right_expr = separated.pop()
            while op == '-' and len(separated) > 1 and not separated[-1].strip():
                right_expr = '-' + right_expr
                separated.pop()
            left_val = self.interpret_expression(op.join(separated), local_vars, allow_recursion)
            return self._operator(op, 0 if left_val is None else left_val,
                                  right_expr, expr, local_vars, allow_recursion), should_return

        if md.get('attribute'):
            variable = m.group('var')
            member = m.group('member')
            if not member:
                member = self.interpret_expression(m.group('member2'), local_vars, allow_recursion)
            arg_str = expr[m.end():]
            if arg_str.startswith('('):
                arg_str, remaining = self._separate_at_paren(arg_str, ')')
            else:
                arg_str, remaining = None, arg_str

            def assertion(cndn, msg):
                """ assert, but without risk of getting optimized out """
                if not cndn:
                    raise ExtractorError('{member} {msg}'.format(**locals()), expr=expr)

            def eval_method():
                if (variable, member) == ('console', 'debug'):
                    return
                types = {
                    'String': compat_str,
                    'Math': float,
                }
                obj = local_vars.get(variable, types.get(variable, NO_DEFAULT))
                if obj is NO_DEFAULT:
                    if variable not in self._objects:
                        self._objects[variable] = self.extract_object(variable)
                    obj = self._objects[variable]

                # Member access
                if arg_str is None:
                    return self._index(obj, member)

                # Function call
                argvals = [
                    self.interpret_expression(v, local_vars, allow_recursion)
                    for v in self._separate(arg_str)]

                if obj == compat_str:
                    if member == 'fromCharCode':
                        assertion(argvals, 'takes one or more arguments')
                        return ''.join(map(chr, argvals))
                    raise self.Exception('Unsupported string method ' + member, expr=expr)
                elif obj == float:
                    if member == 'pow':
                        assertion(len(argvals) == 2, 'takes two arguments')
                        return argvals[0] ** argvals[1]
                    raise self.Exception('Unsupported Math method ' + member, expr=expr)

                if member == 'split':
                    assertion(argvals, 'takes one or more arguments')
                    assertion(len(argvals) == 1, 'with limit argument is not implemented')
                    return obj.split(argvals[0]) if argvals[0] else list(obj)
                elif member == 'join':
                    assertion(isinstance(obj, list), 'must be applied on a list')
                    assertion(len(argvals) == 1, 'takes exactly one argument')
                    return argvals[0].join(obj)
                elif member == 'reverse':
                    assertion(not argvals, 'does not take any arguments')
                    obj.reverse()
                    return obj
                elif member == 'slice':
                    assertion(isinstance(obj, list), 'must be applied on a list')
                    assertion(len(argvals) == 1, 'takes exactly one argument')
                    return obj[argvals[0]:]
                elif member == 'splice':
                    assertion(isinstance(obj, list), 'must be applied on a list')
                    assertion(argvals, 'takes one or more arguments')
                    index, howMany = map(int, (argvals + [len(obj)])[:2])
                    if index < 0:
                        index += len(obj)
                    add_items = argvals[2:]
                    res = []
                    for i in range(index, min(index + howMany, len(obj))):
                        res.append(obj.pop(index))
                    for i, item in enumerate(add_items):
                        obj.insert(index + i, item)
                    return res
                elif member == 'unshift':
                    assertion(isinstance(obj, list), 'must be applied on a list')
                    assertion(argvals, 'takes one or more arguments')
                    for item in reversed(argvals):
                        obj.insert(0, item)
                    return obj
                elif member == 'pop':
                    assertion(isinstance(obj, list), 'must be applied on a list')
                    assertion(not argvals, 'does not take any arguments')
                    if not obj:
                        return
                    return obj.pop()
                elif member == 'push':
                    assertion(argvals, 'takes one or more arguments')
                    obj.extend(argvals)
                    return obj
                elif member == 'forEach':
                    assertion(argvals, 'takes one or more arguments')
                    assertion(len(argvals) <= 2, 'takes at-most 2 arguments')
                    f, this = (argvals + [''])[:2]
                    return [f((item, idx, obj), {'this': this}, allow_recursion) for idx, item in enumerate(obj)]
                elif member == 'indexOf':
                    assertion(argvals, 'takes one or more arguments')
                    assertion(len(argvals) <= 2, 'takes at-most 2 arguments')
                    idx, start = (argvals + [0])[:2]
                    try:
                        return obj.index(idx, start)
                    except ValueError:
                        return -1

                idx = int(member) if isinstance(obj, list) else member
                return obj[idx](argvals, allow_recursion=allow_recursion)

            if remaining:
                ret, should_abort = self.interpret_statement(
                    self._named_object(local_vars, eval_method()) + remaining,
                    local_vars, allow_recursion)
                return ret, should_return or should_abort
            else:
                return eval_method(), should_return

        elif md.get('function'):
            fname = m.group('fname')
            argvals = [self.interpret_expression(v, local_vars, allow_recursion)
                       for v in self._separate(m.group('args'))]
            if fname in local_vars:
                return local_vars[fname](argvals, allow_recursion=allow_recursion), should_return
            elif fname not in self._functions:
                self._functions[fname] = self.extract_function(fname)
            return self._functions[fname](argvals, allow_recursion=allow_recursion), should_return

        raise self.Exception(
            'Unsupported JS expression ' + (expr[:40] if expr != stmt else ''), expr=stmt)

    def interpret_expression(self, expr, local_vars, allow_recursion):
        ret, should_return = self.interpret_statement(expr, local_vars, allow_recursion)
        if should_return:
            raise self.Exception('Cannot return from an expression', expr)
        return ret

    def extract_object(self, objname):
        _FUNC_NAME_RE = r'''(?:[a-zA-Z$0-9]+|"[a-zA-Z$0-9]+"|'[a-zA-Z$0-9]+')'''
        obj = {}
        obj_m = re.search(
            r'''(?x)
                (?<!this\.)%s\s*=\s*{\s*
                    (?P<fields>(%s\s*:\s*function\s*\(.*?\)\s*{.*?}(?:,\s*)?)*)
                }\s*;
            ''' % (re.escape(objname), _FUNC_NAME_RE),
            self.code)
        if not obj_m:
            raise self.Exception('Could not find object ' + objname)
        fields = obj_m.group('fields')
        # Currently, it only supports function definitions
        fields_m = re.finditer(
            r'''(?x)
                (?P<key>%s)\s*:\s*function\s*\((?P<args>(?:%s|,)*)\){(?P<code>[^}]+)}
            ''' % (_FUNC_NAME_RE, _NAME_RE),
            fields)
        for f in fields_m:
            argnames = self.build_arglist(f.group('args'))
            obj[remove_quotes(f.group('key'))] = self.build_function(argnames, f.group('code'))

        return obj

    def extract_function_code(self, funcname):
        """ @returns argnames, code """
        func_m = re.search(
            r'''(?xs)
                (?:
                    function\s+%(name)s|
                    [{;,]\s*%(name)s\s*=\s*function|
                    (?:var|const|let)\s+%(name)s\s*=\s*function
                )\s*
                \((?P<args>[^)]*)\)\s*
                (?P<code>{.+})''' % {'name': re.escape(funcname)},
            self.code)
        code, _ = self._separate_at_paren(func_m.group('code'), '}')  # refine the match
        if func_m is None:
            raise self.Exception('Could not find JS function "{funcname}"'.format(**locals()))
        return self.build_arglist(func_m.group('args')), code

    def extract_function(self, funcname):
        return self.extract_function_from_code(*self.extract_function_code(funcname))

    def extract_function_from_code(self, argnames, code, *global_stack):
        local_vars = {}
        while True:
            mobj = re.search(r'function\((?P<args>[^)]*)\)\s*{', code)
            if mobj is None:
                break
            start, body_start = mobj.span()
            body, remaining = self._separate_at_paren(code[body_start - 1:], '}')
            name = self._named_object(
                local_vars,
                self.extract_function_from_code(
                    self.build_arglist(mobj.group('args')),
                    body, local_vars, *global_stack))
            code = code[:start] + name + remaining
        return self.build_function(argnames, code, local_vars, *global_stack)

    def call_function(self, funcname, *args):
        return self.extract_function(funcname)(args)

    @classmethod
    def build_arglist(cls, arg_text):
        if not arg_text:
            return []
        return list(filter(None, (x.strip() or None for x in cls._separate(arg_text))))

    def build_function(self, argnames, code, *global_stack):
        global_stack = list(global_stack) or [{}]
        argnames = tuple(argnames)

        def resf(args, kwargs={}, allow_recursion=100):
            global_stack[0].update(
                zip_longest(argnames, args, fillvalue=None))
            global_stack[0].update(kwargs)
            var_stack = LocalNameSpace(*global_stack)
            ret, should_abort = self.interpret_statement(code.replace('\n', ''), var_stack, allow_recursion - 1)
            if should_abort:
                return ret
        return resf
