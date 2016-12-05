from __future__ import unicode_literals

import re

from ..utils import ExtractorError
from .tstream import TokenStream

_token_keys = 'null', 'bool', 'id', 'str', 'int', 'float', 'regex'

# TODO support json
class JSInterpreter(object):
    undefined = object()

    def __init__(self, code, objects=None):
        if objects is None:
            objects = {}
        self.code = code
        self._functions = {}
        self._objects = objects

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
            for s in self.statements(token_stream, stack_top - 1):
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
                    token_stream.chk_id(last=True)
                    variables.append(token_value)

                    peek_id, peek_value, peek_pos = token_stream.peek()
                    if peek_id == 'aop':
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
        if peek_id == 'aop':
            token_stream.pop()
            _, op = peek_value
            right = self._assign_expression(token_stream, stack_top - 1)
        else:
            op = None
            right = None
        return ('assign', op, left, right)

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
                    token_stream.chk_id(last=True)
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
        return expr

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
                    name, op = peek_value
                    had_inc = name in ('inc', 'dec')
                    while stack and stack[-1][0] < 16:
                        _, stack_id, stack_op = stack.pop()
                        out.append((stack_id, stack_op))
                    stack.append((16, peek_id, op))
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
                    _, stack_id, stack_op = stack.pop()
                    out.append((stack_id, stack_op))
                stack.append((prec, peek_id, op))
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
                _, stack_id, stack_op = stack.pop()
                out.append((stack_id, stack_op))
            if has_another:
                stack.append((prec, peek_id, op))
                token_stream.pop()

        return ('rpn', out)

    def interpret_statement(self, stmt, local_vars, allow_recursion=100):
        pass

    def interpret_expression(self, expr, local_vars, allow_recursion):
        pass

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
                pass
                # res, abort = self.interpret_statement(stmt, local_vars)
                # if abort:
                #    break
            # return res
        return resf
