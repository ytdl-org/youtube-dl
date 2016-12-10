from __future__ import unicode_literals
from ..compat import compat_str

import re

from ..utils import ExtractorError
from .tstream import TokenStream
from .jsgrammar import Token

_token_keys = set((Token.NULL, Token.BOOL, Token.ID, Token.STR, Token.INT, Token.FLOAT, Token.REGEX))


class Context(object):
    def __init__(self, variables=None, ended=False):
        self.ended = ended
        self.local_vars = {}
        if variables is not None:
            for k, v in dict(variables).items():
                # TODO validate identifiers
                self.local_vars[k] = Reference(v, (self.local_vars, k))


class Reference(object):
    def __init__(self, value, parent=None):
        self._value = value
        self._parent = parent

    def getvalue(self):
        return self._value

    def putvalue(self, value):
        if self._parent is None:
            raise ExtractorError('Trying to set a read-only reference')
        parent, key = self._parent
        if not hasattr(parent, '__setitem__'):
            raise ExtractorError('Unknown reference')
        parent.__setitem__(key, Reference(value, (parent, key)))

    def __repr__(self):
        if self._parent is not None:
            parent, key = self._parent
            return '<Reference value: %s, parent: %s@(0x%x), key: %s>' % (
                str(self._value), parent.__class__.__name__, id(parent), key)
        return '<Reference value: %s, parent: %s>' % (self._value, None)


class JSInterpreter(object):
    # TODO support json
    undefined = object()

    def __init__(self, code, variables=None):
        self.code = code
        self.global_vars = {}
        if variables is not None:
            for k, v in dict(variables).items():
                # TODO validate identifiers
                self.global_vars[k] = Reference(v, (self.global_vars, k))
        self.context = Context(self.global_vars)
        self._context_stack = []

    def _next_statement(self, token_stream, stack_top):
        if stack_top < 0:
            raise ExtractorError('Recursion limit reached')
        # ast
        statement = None

        token_id, token_value, token_pos = token_stream.peek()
        if token_id in (Token.CCLOSE, Token.END):
            # empty statement goes straight here
            return statement
        if token_id is Token.ID and token_value == 'function':
            token_stream.pop()
            token_stream.chk_id()
            token_id, name, token_pos = token_stream.pop()
            token_id, token_value, token_pos = token_stream.pop()
            if token_id is Token.POPEN:
                open_pos = token_pos
            else:
                raise ExtractorError('Expected argument list at %d' % token_pos)

            args = []
            while True:
                token_id, token_value, token_pos = token_stream.peek()
                if token_id is Token.PCLOSE:
                    token_stream.pop()
                    break
                token_stream.chk_id()
                token_stream.pop()
                args.append(token_value)
                token_id, token_value, token_pos = token_stream.peek()
                if token_id is Token.COMMA:
                    token_stream.pop()
                elif token_id is Token.PCLOSE:
                    pass
                elif token_id is Token.END and token_stream.ended:
                    raise ExtractorError('Unbalanced parentheses at %d' % open_pos)
                else:
                    raise ExtractorError('Expected , separator at %d' % token_pos)

            token_id, token_value, token_pos = token_stream.peek()
            if token_id is not Token.COPEN:
                raise ExtractorError('Expected function body at %d' % token_pos)

            statement = (Token.FUNC, name, args, self._next_statement(token_stream, stack_top - 1))
        elif token_id is Token.COPEN:
            # block
            open_pos = token_pos
            token_stream.pop()
            statement_list = []
            while True:
                statement_list.append(self._next_statement(token_stream, stack_top - 1))
                token_stream.pop()
                token_id, token_value, token_pos = token_stream.peek()
                if token_id is Token.CCLOSE:
                    # TODO handle unmatched Token.COPEN
                    break
                elif token_id is Token.END and token_stream.ended:
                    raise ExtractorError('Unbalanced parentheses at %d' % open_pos)
            statement = (Token.BLOCK, statement_list)
        elif token_id is Token.ID:
            # TODO parse label
            if token_value == 'var':
                token_stream.pop()
                variables = []
                init = []
                has_another = True
                while has_another:
                    token_id, token_value, token_pos = token_stream.pop()
                    if token_id is not Token.ID:
                        raise ExtractorError('Missing variable name at %d' % token_pos)
                    token_stream.chk_id(last=True)
                    variables.append(token_value)

                    peek_id, peek_value, peek_pos = token_stream.peek()
                    if peek_id is Token.AOP:
                        token_stream.pop()
                        init.append(self._assign_expression(token_stream, stack_top - 1))
                        peek_id, peek_value, peek_pos = token_stream.peek()
                    else:
                        init.append(JSInterpreter.undefined)

                    if peek_id is Token.END:
                        has_another = False
                    elif peek_id is Token.COMMA:
                        pass
                    else:
                        # FIXME automatic end insertion
                        # - token_id is Token.CCLOSE
                        # - check line terminator
                        # - restricted token
                        raise ExtractorError('Unexpected sequence %s at %d' % (peek_value, peek_pos))
                statement = (Token.VAR, zip(variables, init))
            elif token_value == 'if':
                # TODO parse ifstatement
                raise ExtractorError('Conditional statement is not yet supported at %d' % token_pos)
            elif token_value in ('for', 'do', 'while'):
                # TODO parse iterstatement
                raise ExtractorError('Loops is not yet supported at %d' % token_pos)
            elif token_value in ('break', 'continue'):
                # TODO parse continue, break
                raise ExtractorError('Flow control is not yet supported at %d' % token_pos)
            elif token_value == 'return':
                token_stream.pop()
                peek_id, peek_value, peek_pos = token_stream.peek()
                expr = self._expression(token_stream, stack_top - 1) if peek_id is not Token.END else None
                statement = (Token.RETURN, expr)
                peek_id, peek_value, peek_pos = token_stream.peek()
                if peek_id is not Token.END:
                    # FIXME automatic end insertion
                    raise ExtractorError('Unexpected sequence %s at %d' % (peek_value, peek_pos))
            elif token_value == 'with':
                # TODO parse withstatement
                raise ExtractorError('With statement is not yet supported at %d' % token_pos)
            elif token_value == 'switch':
                # TODO parse switchstatement
                raise ExtractorError('Switch statement is not yet supported at %d' % token_pos)
            elif token_value == 'throw':
                # TODO parse throwstatement
                raise ExtractorError('Throw statement is not yet supported at %d' % token_pos)
            elif token_value == 'try':
                # TODO parse trystatement
                raise ExtractorError('Try statement is not yet supported at %d' % token_pos)
            elif token_value == 'debugger':
                # TODO parse debuggerstatement
                raise ExtractorError('Debugger statement is not yet supported at %d' % token_pos)
        # expr
        if statement is None:
            expr_list = []
            has_another = True
            while has_another:
                peek_id, peek_value, peek_pos = token_stream.peek()
                if not (peek_id is Token.COPEN and peek_id is Token.ID and peek_value == 'function'):
                    expr_list.append(self._assign_expression(token_stream, stack_top - 1))
                    peek_id, peek_value, peek_pos = token_stream.peek()

                if peek_id is Token.END:
                    has_another = False
                elif peek_id is Token.COMMA:
                    pass
                else:
                    # FIXME automatic end insertion
                    raise ExtractorError('Unexpected sequence %s at %d' % (peek_value, peek_pos))

            statement = (Token.EXPR, expr_list)
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
            if peek_id is Token.COMMA:
                token_stream.pop()
            elif peek_id is Token.ID and peek_value == 'yield':
                # TODO parse yield
                raise ExtractorError('Yield statement is not yet supported at %d' % peek_pos)
            else:
                has_another = False
        return (Token.EXPR, exprs)

    def _assign_expression(self, token_stream, stack_top):
        if stack_top < 0:
            raise ExtractorError('Recursion limit reached')

        left = self._conditional_expression(token_stream, stack_top - 1)
        peek_id, peek_value, peek_pos = token_stream.peek()
        if peek_id is Token.AOP:
            token_stream.pop()
            _, op = peek_value
            right = self._assign_expression(token_stream, stack_top - 1)
        else:
            op = None
            right = None
        return (Token.ASSIGN, op, left, right)

    def _member_expression(self, token_stream, stack_top):
        peek_id, peek_value, peek_pos = token_stream.peek()
        if peek_id is Token.ID and peek_value == 'new':
            token_stream.pop()
            target = self._member_expression(token_stream, stack_top - 1)
            args = self._arguments(token_stream, stack_top - 1)
            # Rhino has check for args length
            # Rhino has experimental syntax allowing an object literal to follow a new expression
        else:
            target = self._primary_expression(token_stream, stack_top)
            args = None

        return (Token.MEMBER, target, args, self._member_tail(token_stream, stack_top - 1))

    def _member_tail(self, token_stream, stack_top):
        if stack_top < 0:
            raise ExtractorError('Recursion limit reached')

        peek_id, peek_value, peek_pos = token_stream.peek()
        if peek_id is Token.DOT:
            token_stream.pop()
            peek_id, peek_value, peek_pos = token_stream.peek()
            if peek_id is Token.DOT:
                token_stream.pop()
                peek_id, peek_value, peek_pos = token_stream.peek()
            elif peek_id is Token.POPEN:
                # TODO handle field query
                raise ExtractorError('Field query is not yet supported at %d' % peek_pos)

            if peek_id is Token.ID:
                token_stream.pop()
                return (Token.FIELD, peek_value, self._member_tail(token_stream, stack_top - 1))
            else:
                raise ExtractorError('Identifier name expected at %d' % peek_pos)
        elif peek_id is Token.SOPEN:
            token_stream.pop()
            index = self._expression(token_stream, stack_top - 1)
            token_id, token_value, token_pos = token_stream.pop()
            if token_id is Token.SCLOSE:
                return (Token.ELEM, index, self._member_tail(token_stream, stack_top - 1))
            else:
                raise ExtractorError('Unexpected sequence at %d' % token_pos)
        elif peek_id is Token.POPEN:
            args = self._arguments(token_stream, stack_top - 1)
            return (Token.CALL, args, self._member_tail(token_stream, stack_top - 1))
        else:
            return None

    def _primary_expression(self, token_stream, stack_top):
        if stack_top < 0:
            raise ExtractorError('Recursion limit reached')

        # TODO support let
        peek_id, peek_value, peek_pos = token_stream.peek()
        if peek_id in _token_keys:
            token_stream.pop()
            if peek_id is Token.ID:
                # this
                if peek_value == 'this':
                    return (Token.RSV, 'this')
                # function expr
                elif peek_value == 'function':
                    # TODO parse function expression
                    raise ExtractorError('Function expression is not yet supported at %d' % peek_pos)
                # id
                else:
                    token_stream.chk_id(last=True)
                    return (Token.ID, peek_value)
            # literals
            else:
                return (peek_id, peek_value)
        # array
        elif peek_id is Token.SOPEN:
            return self._array_literal(token_stream, stack_top - 1)
        # object
        elif peek_id is Token.SCLOSE:
            # TODO parse object
            raise ExtractorError('Object literals is not yet supported at %d' % peek_pos)
        # expr
        elif peek_id is Token.POPEN:
            token_stream.pop()
            open_pos = peek_pos
            expr = self._expression(token_stream, stack_top - 1)
            peek_id, peek_value, peek_pos = token_stream.peek()
            if peek_id is not Token.PCLOSE:
                raise ExtractorError('Unbalanced parentheses at %d' % open_pos)
            token_stream.pop()
            return expr
        # empty (probably)
        else:
            return None

    def _arguments(self, token_stream, stack_top):
        if stack_top < 0:
            raise ExtractorError('Recursion limit reached')

        peek_id, peek_value, peek_pos = token_stream.peek()
        if peek_id is Token.POPEN:
            token_stream.pop()
            open_pos = peek_pos
        else:
            return None
        args = []
        while True:
            peek_id, peek_value, peek_pos = token_stream.peek()
            if peek_id is Token.PCLOSE:
                token_stream.pop()
                return args
            # FIXME handle infor
            args.append(self._assign_expression(token_stream, stack_top - 1))
            # TODO parse generator expression
            peek_id, peek_value, peek_pos = token_stream.peek()

            if peek_id is Token.COMMA:
                token_stream.pop()
            elif peek_id is Token.PCLOSE:
                pass
            elif peek_id is Token.END and token_stream.ended:
                raise ExtractorError('Unbalanced parentheses at %d' % open_pos)
            else:
                raise ExtractorError('Expected , separator at %d' % peek_pos)

    def _array_literal(self, token_stream, stack_top):
        if stack_top < 0:
            raise ExtractorError('Recursion limit reached')

        # TODO check no linebreak
        peek_id, peek_value, peek_pos = token_stream.peek()
        if peek_id is not Token.SOPEN:
            raise ExtractorError('Array expected at %d' % peek_pos)
        token_stream.pop()
        elements = []

        has_another = True
        while has_another:
            peek_id, peek_value, peek_pos = token_stream.peek()
            if peek_id is Token.COMMA:
                token_stream.pop()
                elements.append(None)
            elif peek_id is Token.SCLOSE:
                token_stream.pop()
                has_another = False
            elif peek_id is Token.ID and peek_value == 'for':
                # TODO parse array comprehension
                raise ExtractorError('Array comprehension is not yet supported at %d' % peek_pos)
            else:
                elements.append(self._assign_expression(token_stream, stack_top - 1))
                peek_id, peek_value, peek_pos = token_stream.pop()
                if peek_id is Token.SCLOSE:
                    has_another = False
                elif peek_id is not Token.COMMA:
                    raise ExtractorError('Expected , after element at %d' % peek_pos)

        return (Token.ARRAY, elements)

    def _conditional_expression(self, token_stream, stack_top):
        if stack_top < 0:
            raise ExtractorError('Recursion limit reached')

        expr = self._operator_expression(token_stream, stack_top - 1)
        peek_id, peek_value, peek_pos = token_stream.peek()
        if peek_id is Token.HOOK:
            hook_pos = peek_pos
            true_expr = self._assign_expression(token_stream, stack_top - 1)
            peek_id, peek_value, peek_pos = token_stream.peek()
            if peek_id is Token.COLON:
                false_expr = self._assign_expression(token_stream, stack_top - 1)
            else:
                raise ExtractorError('Missing : in conditional expression at %d' % hook_pos)
            return (Token.COND, expr, true_expr, false_expr)
        return expr

    def _operator_expression(self, token_stream, stack_top):
        if stack_top < 0:
            raise ExtractorError('Recursion limit reached')

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
                if peek_id is Token.UOP:
                    name, op = peek_value
                    had_inc = name in (Token.INC, Token.DEC)
                    while stack and stack[-1][0] > 16:
                        _, stack_id, stack_op = stack.pop()
                        out.append((stack_id, stack_op))
                    stack.append((16, peek_id, op))
                    token_stream.pop()
                    peek_id, peek_value, peek_pos = token_stream.peek()
                    if had_inc and peek_id is not Token.ID:
                        raise ExtractorError('Prefix operator has to be followed by an identifier at %d' % peek_pos)
                    has_prefix = peek_id is Token.UOP
                else:
                    has_prefix = False

            left = self._member_expression(token_stream, stack_top - 1)
            out.append(left)

            peek_id, peek_value, peek_pos = token_stream.peek()
            # postfix
            if peek_id is Token.UOP:
                if had_inc:
                    raise ExtractorError('''Can't have prefix and postfix operator at the same time at %d''' % peek_pos)
                name, op = peek_value
                if name in (Token.INC, Token.DEC):
                    prec = 17
                else:
                    raise ExtractorError('Unexpected operator at %d' % peek_pos)
                while stack and stack[-1][0] >= 17:
                    _, stack_id, stack_op = stack.pop()
                    out.append((stack_id, stack_op))
                stack.append((prec, peek_id, op))
                token_stream.pop()
                peek_id, peek_value, peek_pos = token_stream.peek()

            if peek_id is Token.REL:
                name, op = peek_value
            elif peek_id is Token.OP:
                name, op = peek_value
                if name in (Token.MUL, Token.DIV, Token.MOD):
                    prec = 14
                elif name in (Token.ADD, Token.SUB):
                    prec = 13
                elif name in (Token.RSHIFT, Token.LSHIFT, Token.URSHIFT):
                    prec = 12
                elif name is Token.BAND:
                    prec = 9
                elif name is Token.BXOR:
                    prec = 8
                elif name is Token.BOR:
                    prec = 7
                else:
                    raise ExtractorError('Unexpected operator at %d' % peek_pos)
            elif peek_id is Token.LOP:
                name, op = peek_value
                prec = {Token.OR: 5, Token.AND: 6}[name]
            else:
                has_another = False
                prec = 4  # empties stack

            while stack and stack[-1][0] >= prec:
                _, stack_id, stack_op = stack.pop()
                out.append((stack_id, stack_op))
            if has_another:
                stack.append((prec, peek_id, op))
                token_stream.pop()

        return (Token.OPEXPR, out)

    def interpret_statement(self, stmt):
        if stmt is None:
            return None

        name = stmt[0]
        ref = None
        if name == 'funcdecl':
            # TODO interpret funcdecl
            raise ExtractorError('''Can't interpret statement called %s''' % name)
        elif name is Token.BLOCK:
            block = stmt[1]
            for stmt in block:
                s = self.interpret_statement(stmt)
                if s is not None:
                    ref = s.getvalue()
        elif name is Token.VAR:
            for name, value in stmt[1]:
                self.context.local_vars[name] = Reference(self.interpret_expression(value).getvalue(),
                                                          (self.context.local_vars, name))
        elif name is Token.EXPR:
            for expr in stmt[1]:
                ref = self.interpret_expression(expr)
        # if
        # continue, break
        elif name is Token.RETURN:
            ref = self.interpret_statement(stmt[1])
            ref = None if ref is None else ref.getvalue()
            if isinstance(ref, list):
                # TODO test nested arrays
                ref = [elem.getvalue() for elem in ref]

            self.context.ended = True
        # with
        # label
        # switch
        # throw
        # try
        # debugger
        else:
            raise ExtractorError('''Can't interpret statement called %s''' % name)
        return ref

    def interpret_expression(self, expr):
        if expr is None:
            return
        name = expr[0]

        if name is Token.ASSIGN:
            op, left, right = expr[1:]
            if op is None:
                ref = self.interpret_expression(left)
            else:
                # TODO handle undeclared variables (create propery)
                leftref = self.interpret_expression(left)
                leftvalue = leftref.getvalue()
                rightvalue = self.interpret_expression(right).getvalue()
                leftref.putvalue(op(leftvalue, rightvalue))
                # TODO check specs
                ref = leftref

        elif name is Token.EXPR:
            ref = self.interpret_statement(expr)

        elif name is Token.OPEXPR:
            stack = []
            rpn = expr[1][:]
            while rpn:
                token = rpn.pop(0)
                if token[0] in (Token.OP, Token.AOP, Token.UOP, Token.LOP, Token.REL):
                    right = stack.pop()
                    left = stack.pop()
                    stack.append(Reference(token[1](left.getvalue(), right.getvalue())))
                elif token[0] is Token.UOP:
                    right = stack.pop()
                    stack.append(token[1](right.getvalue()))
                else:
                    stack.append(self.interpret_expression(token))
            result = stack.pop()
            if not stack:
                ref = result
            else:
                raise ExtractorError('Expression has too many values')

        elif name is Token.MEMBER:
            # TODO interpret member
            target, args, tail = expr[1:]
            target = self.interpret_expression(target)
            while tail is not None:
                tail_name, tail_value, tail = tail
                if tail_name is Token.FIELD:
                    # TODO interpret field
                    raise ExtractorError('''Can't interpret expression called %s''' % tail_name)
                elif tail_name is Token.ELEM:
                    index = self.interpret_statement(tail_value).getvalue()
                    target = target.getvalue()[index]
                elif tail_name is Token.CALL:
                    # TODO interpret call
                    raise ExtractorError('''Can't interpret expression called %s''' % tail_name)
            ref = target

        elif name is Token.ID:
            # TODO error handling (unknown id)
            ref = self.context.local_vars[expr[1]] if expr[1] in self.context.local_vars else self.global_vars[expr[1]]
        
        # literal
        elif name in _token_keys:
            ref = Reference(expr[1])

        elif name is Token.ARRAY:
            array = []
            for key, elem in enumerate(expr[1]):
                value = self.interpret_expression(elem)
                value._parent = array, key
                array.append(value)
            ref = Reference(array)

        else:
            raise ExtractorError('''Can't interpret expression called %s''' % name)

        return ref

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

    def push_context(self, cx):
        self._context_stack.append(self.context)
        self.context = cx

    def pop_context(self):
        # TODO check underflow
        self.context = self._context_stack.pop()

    def call_function(self, funcname, *args):
        f = self.extract_function(funcname)
        return f(args)

    def build_function(self, argnames, code):
        def resf(args):
            self.push_context(Context(dict(zip(argnames, args))))
            for stmt in self.statements(code):
                res = self.interpret_statement(stmt)
                if self.context.ended:
                    self.pop_context()
                    break
            return res
        return resf
