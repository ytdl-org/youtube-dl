# coding: utf-8
from __future__ import unicode_literals

import itertools
import json
import operator
import re

from functools import update_wrapper, wraps

from .utils import (
    error_to_compat_str,
    ExtractorError,
    float_or_none,
    js_to_json,
    remove_quotes,
    unified_timestamp,
    variadic,
    write_string,
)
from .compat import (
    compat_basestring,
    compat_chr,
    compat_collections_chain_map as ChainMap,
    compat_contextlib_suppress,
    compat_filter as filter,
    compat_itertools_zip_longest as zip_longest,
    compat_map as map,
    compat_numeric_types,
    compat_str,
)


# name JS functions
class function_with_repr(object):
    # from yt_dlp/utils.py, but in this module
    # repr_ is always set
    def __init__(self, func, repr_):
        update_wrapper(self, func)
        self.func, self.__repr = func, repr_

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def __repr__(self):
        return self.__repr


# name JS operators
def wraps_op(op):

    def update_and_rename_wrapper(w):
        f = update_wrapper(w, op)
        # fn names are str in both Py 2/3
        f.__name__ = str('JS_') + f.__name__
        return f

    return update_and_rename_wrapper


# NB In principle NaN cannot be checked by membership.
# Here all NaN values are actually this one, so _NaN is _NaN,
# although _NaN != _NaN. Ditto Infinity.

_NaN = float('nan')
_Infinity = float('inf')


class JS_Undefined(object):
    pass


def _js_bit_op(op):

    def zeroise(x):
        return 0 if x in (None, JS_Undefined, _NaN, _Infinity) else x

    @wraps_op(op)
    def wrapped(a, b):
        return op(zeroise(a), zeroise(b)) & 0xffffffff

    return wrapped


def _js_arith_op(op, div=False):

    @wraps_op(op)
    def wrapped(a, b):
        if JS_Undefined in (a, b):
            return _NaN
        # null, "" --> 0
        a, b = (float_or_none(
            (x.strip() if isinstance(x, compat_basestring) else x) or 0,
            default=_NaN) for x in (a, b))
        if _NaN in (a, b):
            return _NaN
        try:
            return op(a, b)
        except ZeroDivisionError:
            return _NaN if not (div and (a or b)) else _Infinity

    return wrapped


_js_arith_add = _js_arith_op(operator.add)


def _js_add(a, b):
    if not (isinstance(a, compat_basestring) or isinstance(b, compat_basestring)):
        return _js_arith_add(a, b)
    if not isinstance(a, compat_basestring):
        a = _js_toString(a)
    elif not isinstance(b, compat_basestring):
        b = _js_toString(b)
    return operator.concat(a, b)


_js_mod = _js_arith_op(operator.mod)
__js_exp = _js_arith_op(operator.pow)


def _js_exp(a, b):
    if not b:
        return 1  # even 0 ** 0 !!
    return __js_exp(a, b)


def _js_to_primitive(v):
    return (
        ','.join(map(_js_toString, v)) if isinstance(v, list)
        else '[object Object]' if isinstance(v, dict)
        else compat_str(v) if not isinstance(v, (
            compat_numeric_types, compat_basestring))
        else v
    )


def _js_toString(v):
    return (
        'undefined' if v is JS_Undefined
        else 'Infinity' if v == _Infinity
        else 'NaN' if v is _NaN
        else 'null' if v is None
        # bool <= int: do this first
        else ('false', 'true')[v] if isinstance(v, bool)
        else '{0:.7f}'.format(v).rstrip('.0') if isinstance(v, compat_numeric_types)
        else _js_to_primitive(v))


_nullish = frozenset((None, JS_Undefined))


def _js_eq(a, b):
    # NaN != any
    if _NaN in (a, b):
        return False
    # Object is Object
    if isinstance(a, type(b)) and isinstance(b, (dict, list)):
        return operator.is_(a, b)
    # general case
    if a == b:
        return True
    # null == undefined
    a_b = set((a, b))
    if a_b & _nullish:
        return a_b <= _nullish
    a, b = _js_to_primitive(a), _js_to_primitive(b)
    if not isinstance(a, compat_basestring):
        a, b = b, a
    # Number to String: convert the string to a number
    # Conversion failure results in ... false
    if isinstance(a, compat_basestring):
        return float_or_none(a) == b
    return a == b


def _js_neq(a, b):
    return not _js_eq(a, b)


def _js_id_op(op):

    @wraps_op(op)
    def wrapped(a, b):
        if _NaN in (a, b):
            return op(_NaN, None)
        if not isinstance(a, (compat_basestring, compat_numeric_types)):
            a, b = b, a
        # strings are === if ==
        # why 'a' is not 'a': https://stackoverflow.com/a/1504848
        if isinstance(a, (compat_basestring, compat_numeric_types)):
            return a == b if op(0, 0) else a != b
        return op(a, b)

    return wrapped


def _js_comp_op(op):

    @wraps_op(op)
    def wrapped(a, b):
        if JS_Undefined in (a, b):
            return False
        if isinstance(a, compat_basestring):
            b = compat_str(b or 0)
        elif isinstance(b, compat_basestring):
            a = compat_str(a or 0)
        return op(a or 0, b or 0)

    return wrapped


def _js_ternary(cndn, if_true=True, if_false=False):
    """Simulate JS's ternary operator (cndn?if_true:if_false)"""
    if cndn in (False, None, 0, '', JS_Undefined, _NaN):
        return if_false
    return if_true


def _js_unary_op(op):

    @wraps_op(op)
    def wrapped(_, a):
        return op(a)

    return wrapped


# https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/typeof
def _js_typeof(expr):
    with compat_contextlib_suppress(TypeError, KeyError):
        return {
            JS_Undefined: 'undefined',
            _NaN: 'number',
            _Infinity: 'number',
            True: 'boolean',
            False: 'boolean',
            None: 'object',
        }[expr]
    for t, n in (
        (compat_basestring, 'string'),
        (compat_numeric_types, 'number'),
    ):
        if isinstance(expr, t):
            return n
    if callable(expr):
        return 'function'
    # TODO: Symbol, BigInt
    return 'object'


# (op, definition) in order of binding priority, tightest first
# avoid dict to maintain order
# definition None => Defined in JSInterpreter._operator
_OPERATORS = (
    ('>>', _js_bit_op(operator.rshift)),
    ('<<', _js_bit_op(operator.lshift)),
    ('+', _js_add),
    ('-', _js_arith_op(operator.sub)),
    ('*', _js_arith_op(operator.mul)),
    ('%', _js_mod),
    ('/', _js_arith_op(operator.truediv, div=True)),
    ('**', _js_exp),
)

_COMP_OPERATORS = (
    ('===', _js_id_op(operator.is_)),
    ('!==', _js_id_op(operator.is_not)),
    ('==', _js_eq),
    ('!=', _js_neq),
    ('<=', _js_comp_op(operator.le)),
    ('>=', _js_comp_op(operator.ge)),
    ('<', _js_comp_op(operator.lt)),
    ('>', _js_comp_op(operator.gt)),
)

_LOG_OPERATORS = (
    ('|', _js_bit_op(operator.or_)),
    ('^', _js_bit_op(operator.xor)),
    ('&', _js_bit_op(operator.and_)),
)

_SC_OPERATORS = (
    ('?', None),
    ('??', None),
    ('||', None),
    ('&&', None),
)

_UNARY_OPERATORS_X = (
    ('void', _js_unary_op(lambda _: JS_Undefined)),
    ('typeof', _js_unary_op(_js_typeof)),
)

_OPERATOR_RE = '|'.join(map(lambda x: re.escape(x[0]), _OPERATORS + _LOG_OPERATORS))

_NAME_RE = r'[a-zA-Z_$][\w$]*'
_MATCHING_PARENS = dict(zip(*zip('()', '{}', '[]')))
_QUOTES = '\'"/'


class JS_Break(ExtractorError):
    def __init__(self):
        ExtractorError.__init__(self, 'Invalid break')


class JS_Continue(ExtractorError):
    def __init__(self):
        ExtractorError.__init__(self, 'Invalid continue')


class JS_Throw(ExtractorError):
    def __init__(self, e):
        self.error = e
        ExtractorError.__init__(self, 'Uncaught exception ' + error_to_compat_str(e))


class LocalNameSpace(ChainMap):
    def __getitem__(self, key):
        try:
            return super(LocalNameSpace, self).__getitem__(key)
        except KeyError:
            return JS_Undefined

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


class Debugger(object):
    ENABLED = False

    @staticmethod
    def write(*args, **kwargs):
        level = kwargs.get('level', 100)

        def truncate_string(s, left, right=0):
            if s is None or len(s) <= left + right:
                return s
            return '...'.join((s[:left - 3], s[-right:] if right else ''))

        write_string('[debug] JS: {0}{1}\n'.format(
            '  ' * (100 - level),
            ' '.join(truncate_string(compat_str(x), 50, 50) for x in args)))

    @classmethod
    def wrap_interpreter(cls, f):
        @wraps(f)
        def interpret_statement(self, stmt, local_vars, allow_recursion, *args, **kwargs):
            if cls.ENABLED and stmt.strip():
                cls.write(stmt, level=allow_recursion)
            try:
                ret, should_ret = f(self, stmt, local_vars, allow_recursion, *args, **kwargs)
            except Exception as e:
                if cls.ENABLED:
                    if isinstance(e, ExtractorError):
                        e = e.orig_msg
                    cls.write('=> Raises:', e, '<-|', stmt, level=allow_recursion)
                raise
            if cls.ENABLED and stmt.strip():
                if should_ret or repr(ret) != stmt:
                    cls.write(['->', '=>'][should_ret], repr(ret), '<-|', stmt, level=allow_recursion)
            return ret, should_ret
        return interpret_statement


class JSInterpreter(object):
    __named_object_counter = 0

    _OBJ_NAME = '__youtube_dl_jsinterp_obj'

    OP_CHARS = None

    def __init__(self, code, objects=None):
        self.code, self._functions = code, {}
        self._objects = {} if objects is None else objects
        if type(self).OP_CHARS is None:
            type(self).OP_CHARS = self.OP_CHARS = self.__op_chars()

    class Exception(ExtractorError):
        def __init__(self, msg, *args, **kwargs):
            expr = kwargs.pop('expr', None)
            if expr is not None:
                msg = '{0} in: {1!r:.100}'.format(msg.rstrip(), expr)
            super(JSInterpreter.Exception, self).__init__(msg, *args, **kwargs)

    class JS_RegExp(object):
        RE_FLAGS = {
            # special knowledge: Python's re flags are bitmask values, current max 128
            # invent new bitmask values well above that for literal parsing
            # JS 'u' flag is effectively always set (surrogate pairs aren't seen),
            # but \u{...} and \p{...} escapes aren't handled); no additional JS 'v'
            # features are supported
            # TODO: execute matches with these flags (remaining: d, y)
            'd': 1024,  # Generate indices for substring matches
            'g': 2048,  # Global search
            'i': re.I,  # Case-insensitive search
            'm': re.M,  # Multi-line search
            's': re.S,  # Allows . to match newline characters
            'u': re.U,  # Treat a pattern as a sequence of unicode code points
            'v': re.U,  # Like 'u' with extended character class and \p{} syntax
            'y': 4096,  # Perform a "sticky" search that matches starting at the current position in the target string
        }

        def __init__(self, pattern_txt, flags=0):
            if isinstance(flags, compat_str):
                flags, _ = self.regex_flags(flags)
            # First, avoid https://github.com/python/cpython/issues/74534
            self.__self = None
            self.__pattern_txt = pattern_txt.replace('[[', r'[\[')
            self.__flags = flags

        def __instantiate(self):
            if self.__self:
                return
            self.__self = re.compile(self.__pattern_txt, self.__flags)
            # Thx: https://stackoverflow.com/questions/44773522/setattr-on-python2-sre-sre-pattern
            for name in dir(self.__self):
                # Only these? Obviously __class__, __init__.
                # PyPy creates a __weakref__ attribute with value None
                # that can't be setattr'd but also can't need to be copied.
                if name in ('__class__', '__init__', '__weakref__'):
                    continue
                setattr(self, name, getattr(self.__self, name))

        def __getattr__(self, name):
            self.__instantiate()
            # make Py 2.6 conform to its lying documentation
            if name == 'flags':
                self.flags = self.__flags
                return self.flags
            elif name == 'pattern':
                self.pattern = self.__pattern_txt
                return self.pattern
            elif hasattr(self.__self, name):
                v = getattr(self.__self, name)
                setattr(self, name, v)
                return v
            elif name in ('groupindex', 'groups'):
                return 0 if name == 'groupindex' else {}
            raise AttributeError('{0} has no attribute named {1}'.format(self, name))

        @classmethod
        def regex_flags(cls, expr):
            flags = 0
            if not expr:
                return flags, expr
            for idx, ch in enumerate(expr):
                if ch not in cls.RE_FLAGS:
                    break
                flags |= cls.RE_FLAGS[ch]
            return flags, expr[idx + 1:]

    @classmethod
    def __op_chars(cls):
        op_chars = set(';,[')
        for op in cls._all_operators():
            if op[0].isalpha():
                continue
            op_chars.update(op[0])
        return op_chars

    def _named_object(self, namespace, obj):
        self.__named_object_counter += 1
        name = '%s%d' % (self._OBJ_NAME, self.__named_object_counter)
        if callable(obj) and not isinstance(obj, function_with_repr):
            obj = function_with_repr(obj, 'F<%s>' % (self.__named_object_counter, ))
        namespace[name] = obj
        return name

    @classmethod
    def _separate(cls, expr, delim=',', max_split=None, skip_delims=None):
        if not expr:
            return
        # collections.Counter() is ~10% slower in both 2.7 and 3.9
        counters = dict((k, 0) for k in _MATCHING_PARENS.values())
        start, splits, pos, delim_len = 0, 0, 0, len(delim) - 1
        in_quote, escaping, after_op, in_regex_char_group = None, False, True, False
        skipping = 0
        if skip_delims:
            skip_delims = variadic(skip_delims)
        skip_txt = None
        for idx, char in enumerate(expr):
            if skip_txt and idx <= skip_txt[1]:
                continue
            paren_delta = 0
            if not in_quote:
                if char == '/' and expr[idx:idx + 2] == '/*':
                    # skip a comment
                    skip_txt = expr[idx:].find('*/', 2)
                    skip_txt = [idx, idx + skip_txt + 1] if skip_txt >= 2 else None
                    if skip_txt:
                        continue
                if char in _MATCHING_PARENS:
                    counters[_MATCHING_PARENS[char]] += 1
                    paren_delta = 1
                elif char in counters:
                    counters[char] -= 1
                    paren_delta = -1
            if not escaping:
                if char in _QUOTES and in_quote in (char, None):
                    if in_quote or after_op or char != '/':
                        in_quote = None if in_quote and not in_regex_char_group else char
                elif in_quote == '/' and char in '[]':
                    in_regex_char_group = char == '['
            escaping = not escaping and in_quote and char == '\\'
            after_op = not in_quote and (char in cls.OP_CHARS or paren_delta > 0 or (after_op and char.isspace()))

            if char != delim[pos] or any(counters.values()) or in_quote:
                pos = skipping = 0
                continue
            elif skipping > 0:
                skipping -= 1
                continue
            elif pos == 0 and skip_delims:
                here = expr[idx:]
                for s in skip_delims:
                    if here.startswith(s) and s:
                        skipping = len(s) - 1
                        break
                if skipping > 0:
                    continue
            if pos < delim_len:
                pos += 1
                continue
            if skip_txt and skip_txt[0] >= start and skip_txt[1] <= idx - delim_len:
                yield expr[start:skip_txt[0]] + expr[skip_txt[1] + 1: idx - delim_len]
            else:
                yield expr[start: idx - delim_len]
            skip_txt = None
            start, pos = idx + 1, 0
            splits += 1
            if max_split and splits >= max_split:
                break
        if skip_txt and skip_txt[0] >= start:
            yield expr[start:skip_txt[0]] + expr[skip_txt[1] + 1:]
        else:
            yield expr[start:]

    @classmethod
    def _separate_at_paren(cls, expr, delim=None):
        if delim is None:
            delim = expr and _MATCHING_PARENS[expr[0]]
        separated = list(cls._separate(expr, delim, 1))
        if len(separated) < 2:
            raise cls.Exception('No terminating paren {delim} in {expr!r:.5500}'.format(**locals()))
        return separated[0][1:].strip(), separated[1].strip()

    @staticmethod
    def _all_operators(_cached=[]):
        if not _cached:
            _cached.extend(itertools.chain(
                # Ref: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Operator_Precedence
                _SC_OPERATORS, _LOG_OPERATORS, _COMP_OPERATORS, _OPERATORS, _UNARY_OPERATORS_X))
        return _cached

    def _operator(self, op, left_val, right_expr, expr, local_vars, allow_recursion):
        if op in ('||', '&&'):
            if (op == '&&') ^ _js_ternary(left_val):
                return left_val  # short circuiting
        elif op == '??':
            if left_val not in (None, JS_Undefined):
                return left_val
        elif op == '?':
            right_expr = _js_ternary(left_val, *self._separate(right_expr, ':', 1))

        right_val = self.interpret_expression(right_expr, local_vars, allow_recursion)
        opfunc = op and next((v for k, v in self._all_operators() if k == op), None)
        if not opfunc:
            return right_val

        try:
            # print('Eval:', opfunc.__name__, left_val, right_val)
            return opfunc(left_val, right_val)
        except Exception as e:
            raise self.Exception('Failed to evaluate {left_val!r:.50} {op} {right_val!r:.50}'.format(**locals()), expr, cause=e)

    def _index(self, obj, idx, allow_undefined=True):
        if idx == 'length' and isinstance(obj, list):
            return len(obj)
        try:
            return obj[int(idx)] if isinstance(obj, list) else obj[compat_str(idx)]
        except (TypeError, KeyError, IndexError) as e:
            if allow_undefined:
                # when is not allowed?
                return JS_Undefined
            raise self.Exception('Cannot get index {idx!r:.100}'.format(**locals()), expr=repr(obj), cause=e)

    def _dump(self, obj, namespace):
        try:
            return json.dumps(obj)
        except TypeError:
            return self._named_object(namespace, obj)

    # used below
    _VAR_RET_THROW_RE = re.compile(r'''(?x)
        (?P<var>(?:var|const|let)\s)|return(?:\s+|(?=["'])|$)|(?P<throw>throw\s+)
        ''')
    _COMPOUND_RE = re.compile(r'''(?x)
        (?P<try>try)\s*\{|
        (?P<if>if)\s*\(|
        (?P<switch>switch)\s*\(|
        (?P<for>for)\s*\(|
        (?P<while>while)\s*\(
        ''')
    _FINALLY_RE = re.compile(r'finally\s*\{')
    _SWITCH_RE = re.compile(r'switch\s*\(')

    def handle_operators(self, expr, local_vars, allow_recursion):

        for op, _ in self._all_operators():
            # hackety: </> have higher priority than <</>>, but don't confuse them
            skip_delim = (op + op) if op in '<>*?' else None
            if op == '?':
                skip_delim = (skip_delim, '?.')
            separated = list(self._separate(expr, op, skip_delims=skip_delim))
            if len(separated) < 2:
                continue

            right_expr = separated.pop()
            # handle operators that are both unary and binary, minimal BODMAS
            if op in ('+', '-'):
                # simplify/adjust consecutive instances of these operators
                undone = 0
                separated = [s.strip() for s in separated]
                while len(separated) > 1 and not separated[-1]:
                    undone += 1
                    separated.pop()
                if op == '-' and undone % 2 != 0:
                    right_expr = op + right_expr
                elif op == '+':
                    while len(separated) > 1 and set(separated[-1]) <= self.OP_CHARS:
                        right_expr = separated.pop() + right_expr
                    if separated[-1][-1:] in self.OP_CHARS:
                        right_expr = separated.pop() + right_expr
                # hanging op at end of left => unary + (strip) or - (push right)
                left_val = separated[-1] if separated else ''
                for dm_op in ('*', '%', '/', '**'):
                    bodmas = tuple(self._separate(left_val, dm_op, skip_delims=skip_delim))
                    if len(bodmas) > 1 and not bodmas[-1].strip():
                        expr = op.join(separated) + op + right_expr
                        if len(separated) > 1:
                            separated.pop()
                            right_expr = op.join((left_val, right_expr))
                        else:
                            separated = [op.join((left_val, right_expr))]
                            right_expr = None
                        break
                if right_expr is None:
                    continue

            left_val = self.interpret_expression(op.join(separated), local_vars, allow_recursion)
            return self._operator(op, left_val, right_expr, expr, local_vars, allow_recursion), True

    @Debugger.wrap_interpreter
    def interpret_statement(self, stmt, local_vars, allow_recursion=100):
        if allow_recursion < 0:
            raise self.Exception('Recursion limit reached')
        allow_recursion -= 1

        # print('At: ' + stmt[:60])
        should_return = False
        # fails on (eg) if (...) stmt1; else stmt2;
        sub_statements = list(self._separate(stmt, ';')) or ['']
        expr = stmt = sub_statements.pop().strip()

        for sub_stmt in sub_statements:
            ret, should_return = self.interpret_statement(sub_stmt, local_vars, allow_recursion)
            if should_return:
                return ret, should_return

        m = self._VAR_RET_THROW_RE.match(stmt)
        if m:
            expr = stmt[len(m.group(0)):].strip()
            if m.group('throw'):
                raise JS_Throw(self.interpret_expression(expr, local_vars, allow_recursion))
            should_return = not m.group('var')
        if not expr:
            return None, should_return

        if expr[0] in _QUOTES:
            inner, outer = self._separate(expr, expr[0], 1)
            if expr[0] == '/':
                flags, outer = self.JS_RegExp.regex_flags(outer)
                inner = self.JS_RegExp(inner[1:], flags=flags)
            else:
                inner = json.loads(js_to_json(inner + expr[0]))  # , strict=True))
            if not outer:
                return inner, should_return
            expr = self._named_object(local_vars, inner) + outer

        new_kw, _, obj = expr.partition('new ')
        if not new_kw:
            for klass, konstr in (('Date', lambda x: int(unified_timestamp(x, False) * 1000)),
                                  ('RegExp', self.JS_RegExp),
                                  ('Error', self.Exception)):
                if not obj.startswith(klass + '('):
                    continue
                left, right = self._separate_at_paren(obj[len(klass):])
                argvals = self.interpret_iter(left, local_vars, allow_recursion)
                expr = konstr(*argvals)
                if expr is None:
                    raise self.Exception('Failed to parse {klass} {left!r:.100}'.format(**locals()), expr=expr)
                expr = self._dump(expr, local_vars) + right
                break
            else:
                raise self.Exception('Unsupported object {obj:.100}'.format(**locals()), expr=expr)

        for op, _ in _UNARY_OPERATORS_X:
            if not expr.startswith(op):
                continue
            operand = expr[len(op):]
            if not operand or operand[0] != ' ':
                continue
            op_result = self.handle_operators(expr, local_vars, allow_recursion)
            if op_result:
                return op_result[0], should_return

        if expr.startswith('{'):
            inner, outer = self._separate_at_paren(expr)
            # try for object expression (Map)
            sub_expressions = [list(self._separate(sub_expr.strip(), ':', 1)) for sub_expr in self._separate(inner)]
            if all(len(sub_expr) == 2 for sub_expr in sub_expressions):
                return dict(
                    (key_expr if re.match(_NAME_RE, key_expr) else key_expr,
                     self.interpret_expression(val_expr, local_vars, allow_recursion))
                    for key_expr, val_expr in sub_expressions), should_return
            # or statement list
            inner, should_abort = self.interpret_statement(inner, local_vars, allow_recursion)
            if not outer or should_abort:
                return inner, should_abort or should_return
            else:
                expr = self._dump(inner, local_vars) + outer

        if expr.startswith('('):
            m = re.match(r'\((?P<d>[a-z])%(?P<e>[a-z])\.length\+(?P=e)\.length\)%(?P=e)\.length', expr)
            if m:
                # short-cut eval of frequently used `(d%e.length+e.length)%e.length`, worth ~6% on `pytest -k test_nsig`
                outer = None
                inner, should_abort = self._offset_e_by_d(m.group('d'), m.group('e'), local_vars)
            else:
                inner, outer = self._separate_at_paren(expr)
                inner, should_abort = self.interpret_statement(inner, local_vars, allow_recursion)
            if not outer or should_abort:
                return inner, should_abort or should_return
            else:
                expr = self._dump(inner, local_vars) + outer

        if expr.startswith('['):
            inner, outer = self._separate_at_paren(expr)
            name = self._named_object(local_vars, [
                self.interpret_expression(item, local_vars, allow_recursion)
                for item in self._separate(inner)])
            expr = name + outer

        m = self._COMPOUND_RE.match(expr)
        md = m.groupdict() if m else {}
        if md.get('if'):
            cndn, expr = self._separate_at_paren(expr[m.end() - 1:])
            if expr.startswith('{'):
                if_expr, expr = self._separate_at_paren(expr)
            else:
                # may lose ... else ... because of ll.368-374
                if_expr, expr = self._separate_at_paren(' %s;' % (expr,), delim=';')
            else_expr = None
            m = re.match(r'else\s*(?P<block>\{)?', expr)
            if m:
                if m.group('block'):
                    else_expr, expr = self._separate_at_paren(expr[m.end() - 1:])
                else:
                    # handle subset ... else if (...) {...} else ...
                    # TODO: make interpret_statement do this properly, if possible
                    exprs = list(self._separate(expr[m.end():], delim='}', max_split=2))
                    if len(exprs) > 1:
                        if re.match(r'\s*if\s*\(', exprs[0]) and re.match(r'\s*else\b', exprs[1]):
                            else_expr = exprs[0] + '}' + exprs[1]
                            expr = (exprs[2] + '}') if len(exprs) == 3 else None
                        else:
                            else_expr = exprs[0]
                            exprs.append('')
                            expr = '}'.join(exprs[1:])
                    else:
                        else_expr = exprs[0]
                        expr = None
                    else_expr = else_expr.lstrip() + '}'
            cndn = _js_ternary(self.interpret_expression(cndn, local_vars, allow_recursion))
            ret, should_abort = self.interpret_statement(
                if_expr if cndn else else_expr, local_vars, allow_recursion)
            if should_abort:
                return ret, True

        elif md.get('try'):
            try_expr, expr = self._separate_at_paren(expr[m.end() - 1:])
            err = None
            try:
                ret, should_abort = self.interpret_statement(try_expr, local_vars, allow_recursion)
                if should_abort:
                    return ret, True
            except Exception as e:
                # XXX: This works for now, but makes debugging future issues very hard
                err = e

            pending = (None, False)
            m = re.match(r'catch\s*(?P<err>\(\s*{_NAME_RE}\s*\))?\{{'.format(**globals()), expr)
            if m:
                sub_expr, expr = self._separate_at_paren(expr[m.end() - 1:])
                if err:
                    catch_vars = {}
                    if m.group('err'):
                        catch_vars[m.group('err')] = err.error if isinstance(err, JS_Throw) else err
                    catch_vars = local_vars.new_child(m=catch_vars)
                    err, pending = None, self.interpret_statement(sub_expr, catch_vars, allow_recursion)

            m = self._FINALLY_RE.match(expr)
            if m:
                sub_expr, expr = self._separate_at_paren(expr[m.end() - 1:])
                ret, should_abort = self.interpret_statement(sub_expr, local_vars, allow_recursion)
                if should_abort:
                    return ret, True

            ret, should_abort = pending
            if should_abort:
                return ret, True

            if err:
                raise err

        elif md.get('for') or md.get('while'):
            init_or_cond, remaining = self._separate_at_paren(expr[m.end() - 1:])
            if remaining.startswith('{'):
                body, expr = self._separate_at_paren(remaining)
            else:
                switch_m = self._SWITCH_RE.match(remaining)  # FIXME
                if switch_m:
                    switch_val, remaining = self._separate_at_paren(remaining[switch_m.end() - 1:])
                    body, expr = self._separate_at_paren(remaining, '}')
                    body = 'switch(%s){%s}' % (switch_val, body)
                else:
                    body, expr = remaining, ''
            if md.get('for'):
                start, cndn, increment = self._separate(init_or_cond, ';')
                self.interpret_expression(start, local_vars, allow_recursion)
            else:
                cndn, increment = init_or_cond, None
            while _js_ternary(self.interpret_expression(cndn, local_vars, allow_recursion)):
                try:
                    ret, should_abort = self.interpret_statement(body, local_vars, allow_recursion)
                    if should_abort:
                        return ret, True
                except JS_Break:
                    break
                except JS_Continue:
                    pass
                if increment:
                    self.interpret_expression(increment, local_vars, allow_recursion)

        elif md.get('switch'):
            switch_val, remaining = self._separate_at_paren(expr[m.end() - 1:])
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

        if md:
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
            local_vars[var] = _js_add(ret, 1 if sign[0] == '+' else -1)
            if m.group('pre_sign'):
                ret = local_vars[var]
            expr = expr[:start] + self._dump(ret, local_vars) + expr[end:]

        if not expr:
            return None, should_return

        m = re.match(r'''(?x)
            (?P<assign>
                (?P<out>{_NAME_RE})(?:\[(?P<out_idx>(?:.+?\]\s*\[)*.+?)\])?\s*
                (?P<op>{_OPERATOR_RE})?
                =(?!=)(?P<expr>.*)$
            )|(?P<return>
                (?!if|return|true|false|null|undefined|NaN|Infinity)(?P<name>{_NAME_RE})$
            )|(?P<indexing>
                (?P<in>{_NAME_RE})\[(?P<in_idx>(?:.+?\]\s*\[)*.+?)\]$
            )|(?P<attribute>
                (?P<var>{_NAME_RE})(?:(?P<nullish>\?)?\.(?P<member>[^(]+)|\[(?P<member2>[^\]]+)\])\s*
            )|(?P<function>
                (?P<fname>{_NAME_RE})\((?P<args>.*)\)$
            )'''.format(**globals()), expr)
        md = m.groupdict() if m else {}
        if md.get('assign'):
            left_val = local_vars.get(m.group('out'))

            if not m.group('out_idx'):
                local_vars[m.group('out')] = self._operator(
                    m.group('op'), left_val, m.group('expr'), expr, local_vars, allow_recursion)
                return local_vars[m.group('out')], should_return
            elif left_val in (None, JS_Undefined):
                raise self.Exception('Cannot index undefined variable ' + m.group('out'), expr=expr)

            indexes = re.split(r'\]\s*\[', m.group('out_idx'))
            for i, idx in enumerate(indexes, 1):
                idx = self.interpret_expression(idx, local_vars, allow_recursion)
                if i < len(indexes):
                    left_val = self._index(left_val, idx)
            if isinstance(idx, float):
                idx = int(idx)
            left_val[idx] = self._operator(
                m.group('op'), self._index(left_val, idx) if m.group('op') else None,
                m.group('expr'), expr, local_vars, allow_recursion)
            return left_val[idx], should_return

        elif expr.isdigit():
            return int(expr), should_return

        elif expr == 'break':
            raise JS_Break()
        elif expr == 'continue':
            raise JS_Continue()
        elif expr == 'undefined':
            return JS_Undefined, should_return
        elif expr == 'NaN':
            return _NaN, should_return
        elif expr == 'Infinity':
            return _Infinity, should_return

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
            for idx in re.split(r'\]\s*\[', m.group('in_idx')):
                idx = self.interpret_expression(idx, local_vars, allow_recursion)
                val = self._index(val, idx)
            return val, should_return

        op_result = self.handle_operators(expr, local_vars, allow_recursion)
        if op_result:
            return op_result[0], should_return

        if md.get('attribute'):
            variable, member, nullish = m.group('var', 'member', 'nullish')
            if not member:
                member = self.interpret_expression(m.group('member2'), local_vars, allow_recursion)
            arg_str = expr[m.end():]
            if arg_str.startswith('('):
                arg_str, remaining = self._separate_at_paren(arg_str)
            else:
                arg_str, remaining = None, arg_str

            def assertion(cndn, msg):
                """ assert, but without risk of getting optimized out """
                if not cndn:
                    memb = member
                    raise self.Exception('{memb} {msg}'.format(**locals()), expr=expr)

            def eval_method(variable, member):
                if (variable, member) == ('console', 'debug'):
                    if Debugger.ENABLED:
                        Debugger.write(self.interpret_expression('[{}]'.format(arg_str), local_vars, allow_recursion))
                    return
                types = {
                    'String': compat_str,
                    'Math': float,
                    'Array': list,
                }
                obj = local_vars.get(variable)
                if obj in (JS_Undefined, None):
                    obj = types.get(variable, JS_Undefined)
                if obj is JS_Undefined:
                    try:
                        if variable not in self._objects:
                            self._objects[variable] = self.extract_object(variable)
                        obj = self._objects[variable]
                    except self.Exception:
                        if not nullish:
                            raise

                if nullish and obj is JS_Undefined:
                    return JS_Undefined

                # Member access
                if arg_str is None:
                    return self._index(obj, member)

                # Function call
                argvals = [
                    self.interpret_expression(v, local_vars, allow_recursion)
                    for v in self._separate(arg_str)]

                # Fixup prototype call
                if isinstance(obj, type):
                    new_member, rest = member.partition('.')[0::2]
                    if new_member == 'prototype':
                        new_member, func_prototype = rest.partition('.')[0::2]
                        assertion(argvals, 'takes one or more arguments')
                        assertion(isinstance(argvals[0], obj), 'must bind to type {0}'.format(obj))
                        if func_prototype == 'call':
                            obj = argvals.pop(0)
                        elif func_prototype == 'apply':
                            assertion(len(argvals) == 2, 'takes two arguments')
                            obj, argvals = argvals
                            assertion(isinstance(argvals, list), 'second argument must be a list')
                        else:
                            raise self.Exception('Unsupported Function method ' + func_prototype, expr)
                        member = new_member

                if obj is compat_str:
                    if member == 'fromCharCode':
                        assertion(argvals, 'takes one or more arguments')
                        return ''.join(compat_chr(int(n)) for n in argvals)
                    raise self.Exception('Unsupported string method ' + member, expr=expr)
                elif obj is float:
                    if member == 'pow':
                        assertion(len(argvals) == 2, 'takes two arguments')
                        return argvals[0] ** argvals[1]
                    raise self.Exception('Unsupported Math method ' + member, expr=expr)

                if member == 'split':
                    assertion(len(argvals) <= 2, 'takes at most two arguments')
                    if len(argvals) > 1:
                        limit = argvals[1]
                        assertion(isinstance(limit, int) and limit >= 0, 'integer limit >= 0')
                        if limit == 0:
                            return []
                    else:
                        limit = 0
                    if len(argvals) == 0:
                        argvals = [JS_Undefined]
                    elif isinstance(argvals[0], self.JS_RegExp):
                        # avoid re.split(), similar but not enough

                        def where():
                            for m in argvals[0].finditer(obj):
                                yield m.span(0)
                            yield (None, None)

                        def splits(limit=limit):
                            i = 0
                            for j, jj in where():
                                if j == jj == 0:
                                    continue
                                if j is None and i >= len(obj):
                                    break
                                yield obj[i:j]
                                if jj is None or limit == 1:
                                    break
                                limit -= 1
                                i = jj

                        return list(splits())
                    return (
                        obj.split(argvals[0], limit - 1) if argvals[0] and argvals[0] != JS_Undefined
                        else list(obj)[:limit or None])
                elif member == 'join':
                    assertion(isinstance(obj, list), 'must be applied on a list')
                    assertion(len(argvals) <= 1, 'takes at most one argument')
                    return (',' if len(argvals) == 0 else argvals[0]).join(
                        ('' if x in (None, JS_Undefined) else _js_toString(x))
                        for x in obj)
                elif member == 'reverse':
                    assertion(not argvals, 'does not take any arguments')
                    obj.reverse()
                    return obj
                elif member == 'slice':
                    assertion(isinstance(obj, (list, compat_str)), 'must be applied on a list or string')
                    # From [1]:
                    # .slice() - like [:]
                    # .slice(n) - like [n:] (not [slice(n)]
                    # .slice(m, n) - like [m:n] or [slice(m, n)]
                    # [1] https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/slice
                    assertion(len(argvals) <= 2, 'takes between 0 and 2 arguments')
                    if len(argvals) < 2:
                        argvals += (None,)
                    return obj[slice(*argvals)]
                elif member == 'splice':
                    assertion(isinstance(obj, list), 'must be applied on a list')
                    assertion(argvals, 'takes one or more arguments')
                    index, how_many = map(int, (argvals + [len(obj)])[:2])
                    if index < 0:
                        index += len(obj)
                    res = [obj.pop(index)
                           for _ in range(index, min(index + how_many, len(obj)))]
                    obj[index:index] = argvals[2:]
                    return res
                elif member in ('shift', 'pop'):
                    assertion(isinstance(obj, list), 'must be applied on a list')
                    assertion(not argvals, 'does not take any arguments')
                    return obj.pop(0 if member == 'shift' else -1) if len(obj) > 0 else JS_Undefined
                elif member == 'unshift':
                    assertion(isinstance(obj, list), 'must be applied on a list')
                    # not enforced: assertion(argvals, 'takes one or more arguments')
                    obj[0:0] = argvals
                    return len(obj)
                elif member == 'push':
                    # not enforced: assertion(argvals, 'takes one or more arguments')
                    obj.extend(argvals)
                    return len(obj)
                elif member == 'forEach':
                    assertion(argvals, 'takes one or more arguments')
                    assertion(len(argvals) <= 2, 'takes at most 2 arguments')
                    f, this = (argvals + [''])[:2]
                    return [f((item, idx, obj), {'this': this}, allow_recursion) for idx, item in enumerate(obj)]
                elif member == 'indexOf':
                    assertion(argvals, 'takes one or more arguments')
                    assertion(len(argvals) <= 2, 'takes at most 2 arguments')
                    idx, start = (argvals + [0])[:2]
                    try:
                        return obj.index(idx, start)
                    except ValueError:
                        return -1
                elif member == 'charCodeAt':
                    assertion(isinstance(obj, compat_str), 'must be applied on a string')
                    # assertion(len(argvals) == 1, 'takes exactly one argument') # but not enforced
                    idx = argvals[0] if len(argvals) > 0 and isinstance(argvals[0], int) else 0
                    if idx >= len(obj):
                        return None
                    return ord(obj[idx])
                elif member in ('replace', 'replaceAll'):
                    assertion(isinstance(obj, compat_str), 'must be applied on a string')
                    assertion(len(argvals) == 2, 'takes exactly two arguments')
                    # TODO: argvals[1] callable, other Py vs JS edge cases
                    if isinstance(argvals[0], self.JS_RegExp):
                        count = 0 if argvals[0].flags & self.JS_RegExp.RE_FLAGS['g'] else 1
                        assertion(member != 'replaceAll' or count == 0,
                                  'replaceAll must be called with a global RegExp')
                        return argvals[0].sub(argvals[1], obj, count=count)
                    count = ('replaceAll', 'replace').index(member)
                    return re.sub(re.escape(argvals[0]), argvals[1], obj, count=count)

                idx = int(member) if isinstance(obj, list) else member
                return obj[idx](argvals, allow_recursion=allow_recursion)

            if remaining:
                ret, should_abort = self.interpret_statement(
                    self._named_object(local_vars, eval_method(variable, member)) + remaining,
                    local_vars, allow_recursion)
                return ret, should_return or should_abort
            else:
                return eval_method(variable, member), should_return

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

    def interpret_iter(self, list_txt, local_vars, allow_recursion):
        for v in self._separate(list_txt):
            yield self.interpret_expression(v, local_vars, allow_recursion)

    def extract_object(self, objname):
        _FUNC_NAME_RE = r'''(?:[a-zA-Z$0-9]+|"[a-zA-Z$0-9]+"|'[a-zA-Z$0-9]+')'''
        obj = {}
        fields = next(filter(None, (
            obj_m.group('fields') for obj_m in re.finditer(
                r'''(?xs)
                    {0}\s*\.\s*{1}|{1}\s*=\s*\{{\s*
                        (?P<fields>({2}\s*:\s*function\s*\(.*?\)\s*\{{.*?}}(?:,\s*)?)*)
                    }}\s*;
                '''.format(_NAME_RE, re.escape(objname), _FUNC_NAME_RE),
                self.code))), None)
        if not fields:
            raise self.Exception('Could not find object ' + objname)
        # Currently, it only supports function definitions
        for f in re.finditer(
                r'''(?x)
                    (?P<key>%s)\s*:\s*function\s*\((?P<args>(?:%s|,)*)\){(?P<code>[^}]+)}
                ''' % (_FUNC_NAME_RE, _NAME_RE),
                fields):
            argnames = self.build_arglist(f.group('args'))
            name = remove_quotes(f.group('key'))
            obj[name] = function_with_repr(self.build_function(argnames, f.group('code')), 'F<{0}>'.format(name))

        return obj

    @staticmethod
    def _offset_e_by_d(d, e, local_vars):
        """ Short-cut eval: (d%e.length+e.length)%e.length """
        try:
            d = local_vars[d]
            e = local_vars[e]
            e = len(e)
            return _js_mod(_js_mod(d, e) + e, e), False
        except Exception:
            return None, True

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
        if func_m is None:
            raise self.Exception('Could not find JS function "{funcname}"'.format(**locals()))
        code, _ = self._separate_at_paren(func_m.group('code'))  # refine the match
        return self.build_arglist(func_m.group('args')), code

    def extract_function(self, funcname):
        return function_with_repr(
            self.extract_function_from_code(*self.extract_function_code(funcname)),
            'F<%s>' % (funcname,))

    def extract_function_from_code(self, argnames, code, *global_stack):
        local_vars = {}
        while True:
            mobj = re.search(r'function\((?P<args>[^)]*)\)\s*{', code)
            if mobj is None:
                break
            start, body_start = mobj.span()
            body, remaining = self._separate_at_paren(code[body_start - 1:])
            name = self._named_object(local_vars, self.extract_function_from_code(
                [x.strip() for x in mobj.group('args').split(',')],
                body, local_vars, *global_stack))
            code = code[:start] + name + remaining
        return self.build_function(argnames, code, local_vars, *global_stack)

    def call_function(self, funcname, *args):
        return self.extract_function(funcname)(args)

    @classmethod
    def build_arglist(cls, arg_text):
        if not arg_text:
            return []

        def valid_arg(y):
            y = y.strip()
            if not y:
                raise cls.Exception('Missing arg in "%s"' % (arg_text, ))
            return y

        return [valid_arg(x) for x in cls._separate(arg_text)]

    def build_function(self, argnames, code, *global_stack):
        global_stack = list(global_stack) or [{}]
        argnames = tuple(argnames)

        def resf(args, kwargs={}, allow_recursion=100):
            global_stack[0].update(zip_longest(argnames, args, fillvalue=None))
            global_stack[0].update(kwargs)
            var_stack = LocalNameSpace(*global_stack)
            ret, should_abort = self.interpret_statement(code.replace('\n', ' '), var_stack, allow_recursion - 1)
            if should_abort:
                return ret
        return resf
