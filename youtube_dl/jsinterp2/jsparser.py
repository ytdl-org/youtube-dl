from __future__ import unicode_literals

from .jsgrammar import TokenTypes, token_keys
from .tstream import TokenStream, convert_to_unary
from ..utils import ExtractorError


class Parser(object):

    def __init__(self, code, pos=0, stack_size=100):
        super(Parser, self).__init__()
        self.token_stream = TokenStream(code, pos)
        self.stack_top = stack_size
        self._no_in = True

    def parse(self):
        while not self.token_stream.ended:
            yield self._source_element(self.stack_top)

    def _source_element(self, stack_top):
        if stack_top < 0:
            raise ExtractorError('Recursion limit reached')

        token = self.token_stream.peek()
        if token.id is TokenTypes.ID and token.value == 'function':
            source_element = self._function(stack_top - 1)
        else:
            source_element = self._statement(stack_top - 1)

        return source_element

    def _statement(self, stack_top):
        if stack_top < 0:
            raise ExtractorError('Recursion limit reached')

        statement = None
        token = self.token_stream.peek()
        if token.id is TokenTypes.END:
            # empty statement goes straight here
            self.token_stream.pop()
            return statement

        # block
        elif token.id is TokenTypes.COPEN:
            # XXX refactor will deprecate some _statement calls
            open_pos = token.pos
            self.token_stream.pop()
            block = []
            while True:
                token = self.token_stream.peek()
                if token.id is TokenTypes.CCLOSE:
                    self.token_stream.pop()
                    break
                elif token.id is TokenTypes.END and self.token_stream.ended:
                    raise ExtractorError('Unbalanced parentheses at %d' % open_pos)
                block.append(self._statement(stack_top - 1))

            statement = (TokenTypes.BLOCK, block)

        elif token.id is TokenTypes.ID:
            if token.value == 'var':
                self.token_stream.pop()
                variables = []
                init = []
                has_another = True
                while has_another:
                    token = self.token_stream.pop()
                    if token.id is not TokenTypes.ID:
                        raise ExtractorError('Missing variable name at %d' % token.pos)
                    self.token_stream.chk_id(last=True)
                    variables.append(token.value)

                    peek = self.token_stream.peek()
                    if peek.id is TokenTypes.AOP:
                        self.token_stream.pop()
                        init.append(self._assign_expression(stack_top - 1))
                        peek = self.token_stream.peek()
                    else:
                        init.append(None)

                    if peek.id is TokenTypes.END:
                        if self._no_in:
                            self.token_stream.pop()
                        has_another = False
                    elif peek.id is TokenTypes.COMMA:
                        # TODO for not NoIn
                        pass
                    else:
                        # FIXME automatic end insertion
                        # - token_id is Token.CCLOSE
                        # - check line terminator
                        # - restricted token
                        raise ExtractorError('Unexpected sequence at %d' % peek.pos)
                statement = (TokenTypes.VAR, zip(variables, init))

            elif token.value == 'if':
                statement = self._if_statement(stack_top - 1)

            elif token.value == 'for':
                statement = self._for_loop(stack_top - 1)

            elif token.value == 'do':
                statement = self._do_loop(stack_top - 1)

            elif token.value == 'while':
                statement = self._while_loop(stack_top - 1)

            elif token.value in ('break', 'continue'):
                self.token_stream.pop()
                token = {'break': TokenTypes.BREAK, 'continue': TokenTypes.CONTINUE}[token.value]
                peek = self.token_stream.peek()
                # XXX no line break here
                label_name = None
                if peek.id is not TokenTypes.END:
                    self.token_stream.chk_id()
                    label_name = peek.value
                    self.token_stream.pop()
                statement = (token, label_name)
                peek = self.token_stream.peek()
                if peek.id is TokenTypes.END:
                    self.token_stream.pop()
                else:
                    # FIXME automatic end insertion
                    raise ExtractorError('Unexpected sequence at %d' % peek.pos)

            elif token.value == 'return':
                statement = self._return_statement(stack_top - 1)
                peek = self.token_stream.peek()
                if peek.id is TokenTypes.END:
                    self.token_stream.pop()
                else:
                    # FIXME automatic end insertion
                    raise ExtractorError('Unexpected sequence at %d' % peek.pos)

            elif token.value == 'with':
                statement = self._with_statement(stack_top - 1)

            elif token.value == 'switch':
                statement = self._switch_statement(stack_top - 1)

            elif token.value == 'throw':
                self.token_stream.pop()
                # XXX no line break here
                expr = self._expression(stack_top - 1)
                statement = (TokenTypes.RETURN, expr)
                peek = self.token_stream.peek()
                if peek.id is TokenTypes.END:
                    self.token_stream.pop()
                else:
                    # FIXME automatic end insertion
                    raise ExtractorError('Unexpected sequence at %d' % peek.pos)

            elif token.value == 'try':
                statement = self._try_statement(stack_top - 1)

            elif token.value == 'debugger':
                self.token_stream.pop()
                statement = (TokenTypes.DEBUG,)
                peek = self.token_stream.peek()
                if peek.id is TokenTypes.END:
                    self.token_stream.pop()
                else:
                    # FIXME automatic end insertion
                    raise ExtractorError('Unexpected sequence at %d' % peek.pos)
            else:  # label
                # XXX possible refactoring (this is the only branch not popping)
                token = self.token_stream.peek(2)
                if token.id is TokenTypes.COLON:
                    token = self.token_stream.pop(2)
                    self.token_stream.chk_id(last=True)
                    statement = (TokenTypes.LABEL, token.value, self._statement(stack_top - 1))

        # expr
        if statement is None:
            statement = self._expression(stack_top - 1)
            peek = self.token_stream.peek()
            if peek.id is TokenTypes.END:
                self.token_stream.pop()
            else:
                # FIXME automatic end insertion
                raise ExtractorError('Unexpected sequence at %d' % peek.pos)

        return statement

    def _if_statement(self, stack_top):
        if stack_top < 0:
            raise ExtractorError('Recursion limit reached')

        self.token_stream.pop()
        token = self.token_stream.pop()
        if token.id is not TokenTypes.POPEN:
            raise ExtractorError('Missing condition at %d' % token.pos)
        cond_expr = self._expression(stack_top - 1)
        self.token_stream.pop()  # Token.PCLOSE
        true_stmt = self._statement(stack_top - 1)
        false_stmt = None
        token = self.token_stream.peek()
        if token.id is TokenTypes.ID and token.value == 'else':
            self.token_stream.pop()
            false_stmt = self._statement(stack_top - 1)
        return (TokenTypes.IF, cond_expr, true_stmt, false_stmt)

    def _for_loop(self, stack_top):
        if stack_top < 0:
            raise ExtractorError('Recursion limit reached')

        self.token_stream.pop()
        token = self.token_stream.pop()
        if token.id is not TokenTypes.POPEN:
            raise ExtractorError('''Expected '(' at %d''' % token.pos)

        # FIXME set infor True (checked by variable declaration and relation expression)
        self._no_in = False
        token = self.token_stream.peek()
        if token.id is TokenTypes.END:
            init = None
        elif token.id is TokenTypes.ID and token.value == 'var':
            # XXX change it on refactoring variable declaration list
            init = self._statement(stack_top - 1)
        else:
            init = self._expression(stack_top - 1)
        self._no_in = True

        token = self.token_stream.pop()
        if token.id is TokenTypes.ID and token.value == 'in':
            cond = self._expression(stack_top - 1)
            # FIXME further processing of operator 'in' needed for interpretation
            incr = None
        # NOTE ES6 has 'of' operator
        elif token.id is TokenTypes.END:
            token = self.token_stream.peek()
            cond = None if token.id is TokenTypes.END else self._expression(stack_top - 1)

            token = self.token_stream.pop()
            if token.id is not TokenTypes.END:
                raise ExtractorError('''Expected ';' at %d''' % token.pos)

            token = self.token_stream.peek()
            incr = None if token.id is TokenTypes.END else self._expression(stack_top - 1)
        else:
            raise ExtractorError('Invalid condition in for loop initialization at %d' % token.pos)
        token = self.token_stream.pop()
        if token.id is not TokenTypes.PCLOSE:
            raise ExtractorError('''Expected ')' at %d''' % token.pos)
        body = self._statement(stack_top - 1)
        return (TokenTypes.FOR, init, cond, incr, body)

    def _do_loop(self, stack_top):
        if stack_top < 0:
            raise ExtractorError('Recursion limit reached')

        self.token_stream.pop()
        body = self._statement(stack_top - 1)
        token = self.token_stream.pop()
        if token.id is not TokenTypes.ID and token.value != 'while':
            raise ExtractorError('''Expected 'while' at %d''' % token.pos)
        token = self.token_stream.pop()
        if token.id is not TokenTypes.POPEN:
            raise ExtractorError('''Expected '(' at %d''' % token.pos)
        expr = self._expression(stack_top - 1)
        token = self.token_stream.pop()
        if token.id is not TokenTypes.PCLOSE:
            raise ExtractorError('''Expected ')' at %d''' % token.pos)
        peek = self.token_stream.peek()
        if peek.id is TokenTypes.END:
            self.token_stream.pop()
        else:
            # FIXME automatic end insertion
            raise ExtractorError('''Expected ';' at %d''' % peek.pos)
        return (TokenTypes.DO, expr, body)

    def _while_loop(self, stack_top):
        if stack_top < 0:
            raise ExtractorError('Recursion limit reached')

        self.token_stream.pop()
        token = self.token_stream.pop()
        if token.id is not TokenTypes.POPEN:
            raise ExtractorError('''Expected '(' at %d''' % token.pos)
        expr = self._expression(stack_top - 1)
        token = self.token_stream.pop()
        if token.id is not TokenTypes.PCLOSE:
            raise ExtractorError('''Expected ')' at %d''' % token.pos)
        body = self._statement(stack_top)
        return (TokenTypes.WHILE, expr, body)

    def _return_statement(self, stack_top):
        if stack_top < 0:
            raise ExtractorError('Recursion limit reached')

        self.token_stream.pop()
        peek = self.token_stream.peek()
        # XXX no line break here
        expr = self._expression(stack_top - 1) if peek.id is not TokenTypes.END else None
        return (TokenTypes.RETURN, expr)

    def _with_statement(self, stack_top):
        if stack_top < 0:
            raise ExtractorError('Recursion limit reached')

        self.token_stream.pop()
        token = self.token_stream.pop()
        if token.id is not TokenTypes.POPEN:
            raise ExtractorError('Missing expression at %d' % token.pos)
        expr = self._expression(stack_top - 1)
        self.token_stream.pop()  # Token.PCLOSE
        return (TokenTypes.WITH, expr, self._statement(stack_top - 1))

    def _switch_statement(self, stack_top):
        if stack_top < 0:
            raise ExtractorError('Recursion limit reached')

        self.token_stream.pop()
        token = self.token_stream.pop()
        if token.id is not TokenTypes.POPEN:
            raise ExtractorError('Missing expression at %d' % token.pos)
        discriminant = self._expression(stack_top - 1)
        self.token_stream.pop()  # Token.PCLOSE
        token = self.token_stream.pop()
        if token.id is not TokenTypes.COPEN:
            raise ExtractorError('Missing case block at %d' % token.pos)
        open_pos = token.pos
        has_default = False
        block = []
        while True:
            token = self.token_stream.peek()
            if token.id is TokenTypes.CCLOSE:
                break
            elif token.id is TokenTypes.ID and token.value == 'case':
                self.token_stream.pop()
                expr = self._expression(stack_top - 1)

            elif token.id is TokenTypes.ID and token.value == 'default':
                if has_default:
                    raise ExtractorError('Multiple default clause')
                self.token_stream.pop()
                has_default = True
                expr = None

            elif token.id is TokenTypes.END and self.token_stream.ended:
                raise ExtractorError('Unbalanced parentheses at %d' % open_pos)
            else:
                raise ExtractorError('Unexpected sequence at %d, default or case clause is expected' %
                                     token.pos)

            token = self.token_stream.pop()
            if token.id is not TokenTypes.COLON:
                raise ExtractorError('''Unexpected sequence at %d, ':' is expected''' % token.pos)

            statement_list = []
            while True:
                token = self.token_stream.peek()
                if token.id == TokenTypes.CCLOSE or (
                        token.id is TokenTypes.ID and (token.value in ('default', 'case'))):
                    break
                elif token.id is TokenTypes.END and self.token_stream.ended:
                    raise ExtractorError('Unbalanced parentheses at %d' % open_pos)
                statement_list.append(self._statement(stack_top - 1))

            block.append((expr, statement_list))
        self.token_stream.pop()
        return (TokenTypes.SWITCH, discriminant, block)

    def _try_statement(self, stack_top):
        if stack_top < 0:
            raise ExtractorError('Recursion limit reached')

        self.token_stream.pop()
        token = self.token_stream.peek()
        if token.id is not TokenTypes.COPEN:
            raise ExtractorError('Block is expected at %d' % token.pos)
        try_block = self._statement(stack_top - 1)
        token = self.token_stream.pop()
        catch_block = None
        if token.id is TokenTypes.ID and token.value == 'catch':
            token = self.token_stream.peek()
            if token.id is not TokenTypes.POPEN:
                raise ExtractorError('Catch clause is missing an identifier at %d' % token.pos)
            self.token_stream.pop()
            self.token_stream.chk_id()
            error = self.token_stream.pop()
            token = self.token_stream.pop()
            if token.id is not TokenTypes.PCLOSE:
                raise ExtractorError('Catch clause expects a single identifier at %d' % token.pos)
            token = self.token_stream.peek()
            if token.id is not TokenTypes.COPEN:
                raise ExtractorError('Block is expected at %d' % token.pos)
            catch_block = (error.value, self._statement(stack_top - 1))
        finally_block = None
        if token.id is TokenTypes.ID and token.value == 'finally':
            token = self.token_stream.peek()
            if token.id is not TokenTypes.COPEN:
                raise ExtractorError('Block is expected at %d' % token.pos)
            finally_block = self._statement(stack_top - 1)
        if catch_block is None and finally_block is None:
            raise ExtractorError('Try statement is expecting catch or finally at %d' % token.pos)
        return (TokenTypes.TRY, try_block, catch_block, finally_block)

    def _expression(self, stack_top):
        if stack_top < 0:
            raise ExtractorError('Recursion limit reached')

        expr_list = []
        has_another = True
        while has_another:
            expr_list.append(self._assign_expression(stack_top - 1))
            peek = self.token_stream.peek()
            if peek.id is TokenTypes.COMMA:
                self.token_stream.pop()
            elif peek.id is TokenTypes.ID and peek.value == 'yield':
                # TODO parse yield
                raise ExtractorError('Yield statement is not yet supported at %d' % peek.pos)
            else:
                has_another = False
        return (TokenTypes.EXPR, expr_list)

    def _assign_expression(self, stack_top):
        if stack_top < 0:
            raise ExtractorError('Recursion limit reached')

        left = self._conditional_expression(stack_top - 1)
        peek = self.token_stream.peek()
        if peek.id is TokenTypes.AOP:
            self.token_stream.pop()
            _, op = peek.value
            right = self._assign_expression(stack_top - 1)
        else:
            op = None
            right = None
        return (TokenTypes.ASSIGN, op, left, right)

    def _member_expression(self, stack_top):
        if stack_top < 0:
            raise ExtractorError('Recursion limit reached')

        peek = self.token_stream.peek()
        if peek.id is TokenTypes.ID and peek.value == 'new':
            self.token_stream.pop()
            target = self._member_expression(stack_top - 1)
            args = self._arguments(stack_top - 1)
            # Rhino has check for args length
            # Rhino has experimental syntax allowing an object literal to follow a new expression
        else:
            target = self._primary_expression(stack_top - 1)
            args = None

        return (TokenTypes.MEMBER, target, args, self._member_tail(stack_top - 1))

    def _member_tail(self, stack_top):
        if stack_top < 0:
            raise ExtractorError('Recursion limit reached')

        peek = self.token_stream.peek()
        if peek.id is TokenTypes.DOT:
            self.token_stream.pop()
            peek = self.token_stream.peek()
            if peek.id is TokenTypes.DOT:
                self.token_stream.pop()
                peek = self.token_stream.peek()
            elif peek.id is TokenTypes.POPEN:
                # TODO parse field query
                raise ExtractorError('Field query is not yet supported at %d' % peek.pos)

            if peek.id is TokenTypes.ID:
                self.token_stream.pop()
                return (TokenTypes.FIELD, peek.value, self._member_tail(stack_top - 1))
            else:
                raise ExtractorError('Identifier name expected at %d' % peek.pos)
        elif peek.id is TokenTypes.SOPEN:
            self.token_stream.pop()
            index = self._expression(stack_top - 1)
            token = self.token_stream.pop()
            if token.id is TokenTypes.SCLOSE:
                return (TokenTypes.ELEM, index, self._member_tail(stack_top - 1))
            else:
                raise ExtractorError('Unexpected sequence at %d' % token.pos)
        elif peek.id is TokenTypes.POPEN:
            args = self._arguments(stack_top - 1)
            return (TokenTypes.CALL, args, self._member_tail(stack_top - 1))
        else:
            return None

    def _primary_expression(self, stack_top):
        if stack_top < 0:
            raise ExtractorError('Recursion limit reached')

        # TODO support let
        peek = self.token_stream.peek()
        if peek.id in token_keys:
            if peek.id is TokenTypes.ID:
                # this
                if peek.value == 'this':
                    self.token_stream.pop()
                    return (TokenTypes.RSV, 'this')
                # function expr
                elif peek.value == 'function':
                    return self._function(stack_top - 1, True)
                # id
                else:
                    self.token_stream.chk_id()
                    self.token_stream.pop()
                    return (TokenTypes.ID, peek.value)
            # literals
            else:
                self.token_stream.pop()
                return (peek.id, peek.value)
        # array
        elif peek.id is TokenTypes.SOPEN:
            return self._array_literal(stack_top - 1)
        # object
        elif peek.id is TokenTypes.COPEN:
            return self._object_literal(stack_top)
        # expr
        elif peek.id is TokenTypes.POPEN:
            self.token_stream.pop()
            open_pos = peek.pos
            expr = self._expression(stack_top - 1)
            peek = self.token_stream.peek()
            if peek.id is not TokenTypes.PCLOSE:
                raise ExtractorError('Unbalanced parentheses at %d' % open_pos)
            self.token_stream.pop()
            return expr
        else:
            raise ExtractorError('Syntax error at %d' % peek.pos)

    def _function(self, stack_top, is_expr=False):
        if stack_top < 0:
            raise ExtractorError('Recursion limit reached')

        self.token_stream.pop()
        token = self.token_stream.peek()

        name = None
        if token.id is TokenTypes.ID:
            self.token_stream.chk_id()
            name = self.token_stream.pop().value
            token = self.token_stream.peek()
        elif not is_expr:
            raise ExtractorError('Function declaration at %d is missing identifier' % token.pos)

        if token.id is not TokenTypes.POPEN:
            raise ExtractorError('Expected argument list at %d' % token.pos)

        # args
        self.token_stream.pop()
        open_pos = token.pos
        args = []
        while True:
            token = self.token_stream.peek()
            if token.id is TokenTypes.PCLOSE:
                self.token_stream.pop()
                break
            self.token_stream.chk_id()
            self.token_stream.pop()
            args.append(token.value)
            token = self.token_stream.peek()
            if token.id is TokenTypes.COMMA:
                self.token_stream.pop()
            elif token.id is TokenTypes.PCLOSE:
                pass
            elif token.id is TokenTypes.END and self.token_stream.ended:
                raise ExtractorError('Unbalanced parentheses at %d' % open_pos)
            else:
                raise ExtractorError('Expected , separator at %d' % token.pos)

        token = self.token_stream.peek()
        if token.id is not TokenTypes.COPEN:
            raise ExtractorError('Expected function body at %d' % token.pos)

        return (TokenTypes.FUNC, name, args, (self._function_body(stack_top - 1)))

    def _function_body(self, stack_top):
        if stack_top < 0:
            raise ExtractorError('Recursion limit reached')

        open_pos = self.token_stream.pop().pos
        body = []
        while True:
            token = self.token_stream.peek()
            if token.id is TokenTypes.CCLOSE:
                self.token_stream.pop()
                break
            elif token.id is TokenTypes.END and self.token_stream.ended:
                raise ExtractorError('Unbalanced parentheses at %d' % open_pos)
            body.append(self._source_element(stack_top - 1))

        return body

    def _arguments(self, stack_top):
        if stack_top < 0:
            raise ExtractorError('Recursion limit reached')

        peek = self.token_stream.peek()
        if peek.id is TokenTypes.POPEN:
            self.token_stream.pop()
            open_pos = peek.pos
        else:
            return None
        args = []
        while True:
            peek = self.token_stream.peek()
            if peek.id is TokenTypes.PCLOSE:
                self.token_stream.pop()
                return args
            # FIXME handle infor
            args.append(self._assign_expression(stack_top - 1))
            # TODO parse generator expression
            peek = self.token_stream.peek()

            if peek.id is TokenTypes.COMMA:
                self.token_stream.pop()
            elif peek.id is TokenTypes.PCLOSE:
                pass
            elif peek.id is TokenTypes.END and self.token_stream.ended:
                raise ExtractorError('Unbalanced parentheses at %d' % open_pos)
            else:
                raise ExtractorError('''Expected ',' separator at %d''' % peek.pos)

    def _array_literal(self, stack_top):
        if stack_top < 0:
            raise ExtractorError('Recursion limit reached')

        # XXX check no linebreak here
        peek = self.token_stream.peek()
        if peek.id is not TokenTypes.SOPEN:
            raise ExtractorError('Array expected at %d' % peek.pos)
        self.token_stream.pop()
        elements = []

        has_another = True
        while has_another:
            peek = self.token_stream.peek()
            if peek.id is TokenTypes.COMMA:
                self.token_stream.pop()
                elements.append(None)
            elif peek.id is TokenTypes.SCLOSE:
                self.token_stream.pop()
                has_another = False
            elif peek.id is TokenTypes.ID and peek.value == 'for':
                # TODO parse array comprehension
                raise ExtractorError('Array comprehension is not yet supported at %d' % peek.pos)
            else:
                elements.append(self._assign_expression(stack_top - 1))
                peek = self.token_stream.pop()
                if peek.id is TokenTypes.SCLOSE:
                    has_another = False
                elif peek.id is not TokenTypes.COMMA:
                    raise ExtractorError('''Expected ',' after element at %d''' % peek.pos)

        return (TokenTypes.ARRAY, elements)

    def _object_literal(self, stack_top):
        if stack_top < 0:
            raise ExtractorError('Recursion limit reached')

        open_pos = self.token_stream.pop().pos
        property_list = []
        while True:
            token = self.token_stream.pop()
            if token.id is TokenTypes.CCLOSE:
                break
            elif token.id is TokenTypes.COMMA:
                continue
            elif token.id is TokenTypes.ID and token.value in ('get', 'set'):
                is_set = token.id is TokenTypes.ID and token.value == 'set'

                token = self.token_stream.pop()
                if token.id not in (TokenTypes.ID, TokenTypes.STR, TokenTypes.INT, TokenTypes.FLOAT):
                    raise ExtractorError('Property name is expected at %d' % token.pos)
                property_name = token.value
                token = self.token_stream.pop()
                if token.id is not TokenTypes.POPEN:
                    raise ExtractorError('''Expected '(' at %d''' % token.pos)

                if is_set:
                    self.token_stream.chk_id()
                    arg = self.token_stream.pop().value

                token = self.token_stream.pop()
                if token.id is not TokenTypes.PCLOSE:
                    raise ExtractorError('''Expected ')' at %d''' % token.pos)

                if is_set:
                    desc = (TokenTypes.PROPSET, arg, self._function_body(stack_top - 1))
                else:
                    desc = (TokenTypes.PROPGET, self._function_body(stack_top - 1))

            elif token.id in (TokenTypes.ID, TokenTypes.STR, TokenTypes.INT, TokenTypes.FLOAT):
                property_name = token.value
                token = self.token_stream.pop()
                if token.id is not TokenTypes.COLON:
                    raise ExtractorError('Property name is expected at %d' % token.pos)

                desc = (TokenTypes.PROPVALUE, self._assign_expression(stack_top - 1))

            elif self.token_stream.ended:
                raise ExtractorError('Unmatched parentheses at %d' % open_pos)
            else:
                raise ExtractorError('Property assignment is expected at %d' % token.pos)

            property_list.append((property_name, desc))

        return (TokenTypes.OBJECT, property_list)

    def _conditional_expression(self, stack_top):
        if stack_top < 0:
            raise ExtractorError('Recursion limit reached')

        expr = self._operator_expression(stack_top - 1)
        peek = self.token_stream.peek()
        if peek.id is TokenTypes.HOOK:
            hook_pos = peek.pos
            true_expr = self._assign_expression(stack_top - 1)
            peek = self.token_stream.peek()
            if peek.id is TokenTypes.COLON:
                false_expr = self._assign_expression(stack_top - 1)
            else:
                raise ExtractorError('Missing : in conditional expression at %d' % hook_pos)
            return (TokenTypes.COND, expr, true_expr, false_expr)
        return expr

    def _operator_expression(self, stack_top):
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

        while True:
            had_inc = False
            has_prefix = True
            while has_prefix:
                token = self.token_stream.peek()
                peek_id = token.id
                peek_value = token.value
                if peek_id is TokenTypes.OP and peek_value[0] in (TokenTypes.ADD, TokenTypes.SUB):
                    # any binary operators will be consumed later
                    peek_id = TokenTypes.UOP
                    peek_value = convert_to_unary(peek_value)
                if peek_id is TokenTypes.UOP:
                    name, op = peek_value
                    had_inc = name in (TokenTypes.INC, TokenTypes.DEC)
                    if had_inc:
                        peek_id = TokenTypes.PREFIX
                    while stack and stack[-1][0] > 16:
                        _, stack_id, stack_op = stack.pop()
                        out.append((stack_id, stack_op))
                    stack.append((16, peek_id, op))
                    self.token_stream.pop()
                    token = self.token_stream.peek()
                    if had_inc and token.id is not TokenTypes.ID:
                        raise ExtractorError('Prefix operator has to be followed by an identifier at %d' % token.pos)
                    has_prefix = token.id is TokenTypes.UOP
                else:
                    has_prefix = False

            left = self._member_expression(stack_top - 1)
            out.append(left)

            token = self.token_stream.peek()
            # postfix
            if token.id is TokenTypes.UOP:
                if had_inc:
                    raise ExtractorError('''Can't have prefix and postfix operator at the same time at %d''' % token.pos)
                name, op = token.value
                if name in (TokenTypes.INC, TokenTypes.DEC):
                    peek_id = TokenTypes.POSTFIX
                    prec = 17
                else:
                    raise ExtractorError('Unexpected operator at %d' % token.pos)
                while stack and stack[-1][0] >= 17:
                    _, stack_id, stack_op = stack.pop()
                    out.append((stack_id, stack_op))
                stack.append((prec, peek_id, op))
                self.token_stream.pop()
                token = self.token_stream.peek()

            if token.id is TokenTypes.REL:
                name, op = token.value
                prec = 11
            elif token.id is TokenTypes.OP:
                name, op = token.value
                if name in (TokenTypes.MUL, TokenTypes.DIV, TokenTypes.MOD):
                    prec = 14
                elif name in (TokenTypes.ADD, TokenTypes.SUB):
                    prec = 13
                elif name in (TokenTypes.RSHIFT, TokenTypes.LSHIFT, TokenTypes.URSHIFT):
                    prec = 12
                elif name is TokenTypes.BAND:
                    prec = 9
                elif name is TokenTypes.BXOR:
                    prec = 8
                elif name is TokenTypes.BOR:
                    prec = 7
                else:
                    raise ExtractorError('Unexpected operator at %d' % token.pos)
            elif token.id is TokenTypes.LOP:
                name, op = token.value
                prec = {TokenTypes.OR: 5, TokenTypes.AND: 6}[name]
            else:
                op = None
                prec = 4  # empties stack

            while stack and stack[-1][0] >= prec:
                _, stack_id, stack_op = stack.pop()
                out.append((stack_id, stack_op))
            if op is None:
                break
            else:
                stack.append((prec, token.id, op))
                self.token_stream.pop()

        return (TokenTypes.OPEXPR, out)
