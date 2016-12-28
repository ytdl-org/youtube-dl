from __future__ import unicode_literals

import re

from ..compat import compat_str
from ..utils import ExtractorError
from .jsparser import Parser
from .jsgrammar import Token, token_keys


class Context(object):
    def __init__(self, variables=None, ended=False):
        self.ended = ended
        self.no_in = True
        self.local_vars = {}
        if variables is not None:
            for k, v in dict(variables).items():
                # XXX validate identifiers
                self.local_vars[k] = Reference(v, (self.local_vars, k))


class Reference(object):
    def __init__(self, value, parent=None):
        self._value = value
        self._parent = parent

    def getvalue(self, deep=False):
        value = self._value
        if deep:
            if isinstance(self._value, (list, tuple)):
                # TODO test nested arrays
                value = [elem.getvalue() for elem in self._value]
            elif isinstance(self._value, dict):
                value = {}
                for key, prop in self._value.items():
                    value[key] = prop.getvalue()

        return value

    def putvalue(self, value):
        if self._parent is None:
            raise ExtractorError('Trying to set a read-only reference')
        parent, key = self._parent
        if not hasattr(parent, '__setitem__'):
            raise ExtractorError('Unknown reference')
        parent.__setitem__(key, Reference(value, (parent, key)))
        self._value = value
        return value

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
                # XXX validate identifiers
                self.global_vars[k] = self.create_reference(v, (self.global_vars, k))
        self._context = Context()
        self._context_stack = []

    @property
    def this(self):
        return self._context.local_vars

    def create_reference(self, value, parent_key):
        if isinstance(value, dict):
            o = {}
            for k, v in value.items():
                o[k] = self.create_reference(v, (o, k))
        elif isinstance(value, (list, tuple, set)):
            o = []
            for k, v in enumerate(value):
                o[k] = self.create_reference(v, (o, k))
        elif isinstance(value, (int, float, compat_str, bool, re._pattern_type)) or value is None:
            o = value
        else:
            raise ExtractorError('Unsupported type, %s in variables' % type(value))

        return Reference(o, parent_key)

    def interpret_statement(self, stmt):
        if stmt is None:
            return None

        name = stmt[0]
        ref = None
        if name == Token.FUNC:
            name, args, body = stmt[1:]
            if name is not None:
                if self._context_stack:
                    self.this[name] = Reference(self.build_function(args, body), (self.this, name))
                else:
                    self.global_vars[name] = Reference(self.build_function(args, body), (self.this, name))
            else:
                raise ExtractorError('Function expression is not yet implemented')
        elif name is Token.BLOCK:
            block = stmt[1]
            for stmt in block:
                s = self.interpret_statement(stmt)
                if s is not None:
                    ref = s.getvalue()
        elif name is Token.VAR:
            for name, value in stmt[1]:
                value = self.interpret_expression(value).getvalue() if value is not None else self.undefined
                self.this[name] = Reference(value, (self.this, name))
        elif name is Token.EXPR:
            for expr in stmt[1]:
                ref = self.interpret_expression(expr)
        # if
        # continue, break
        elif name is Token.RETURN:
            ref = self.interpret_statement(stmt[1])
            self._context.ended = True
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
                try:
                    leftref = self.interpret_expression(left)
                except KeyError:
                    lname = left[0]
                    key = None
                    if lname is Token.OPEXPR and len(left[1]) == 1:
                        lname = left[1][0][0]
                        if lname is Token.MEMBER:
                            lid, args, tail = left[1][0][1:]
                            if lid[0] is Token.ID and args is None and tail is None:
                                key = lid[1]
                    if key is not None:
                        u = Reference(self.undefined, (self.this, key))
                        leftref = self.this[key] = u
                    else:
                        raise ExtractorError('Invalid left-hand side in assignment')
                leftvalue = leftref.getvalue()
                rightvalue = self.interpret_expression(right).getvalue()
                leftref.putvalue(op(leftvalue, rightvalue))
                # XXX check specs what to return
                ref = leftref

        elif name is Token.EXPR:
            ref = self.interpret_statement(expr)

        elif name is Token.OPEXPR:
            stack = []
            postfix = []
            rpn = expr[1][:]
            # FIXME support pre- and postfix operators
            while rpn:
                token = rpn.pop(0)
                # XXX relation 'in' 'instanceof'
                if token[0] in (Token.OP, Token.AOP, Token.LOP, Token.REL):
                    right = stack.pop()
                    left = stack.pop()
                    stack.append(Reference(token[1](left.getvalue(), right.getvalue())))
                # XXX add unary operator 'delete', 'void', 'instanceof'
                elif token[0] is Token.UOP:
                    right = stack.pop()
                    stack.append(Reference(token[1](right.getvalue())))
                elif token[0] is Token.PREFIX:
                    right = stack.pop()
                    stack.append(Reference(right.putvalue(token[1](right.getvalue()))))
                elif token[0] is Token.POSTFIX:
                    postfix.append((stack[-1], token[1]))
                else:
                    stack.append(self.interpret_expression(token))
            result = stack.pop()
            if not stack:
                for operand, op in postfix:
                    operand.putvalue(op(operand.getvalue()))
                ref = result
            else:
                raise ExtractorError('Expression has too many values')

        elif name is Token.MEMBER:
            # TODO interpret member
            target, args, tail = expr[1:]
            target = self.interpret_expression(target)
            if args is not None:
                # TODO interpret NewExpression
                pass
            while tail is not None:
                tail_name, tail_value, tail = tail
                if tail_name is Token.FIELD:
                    target = target.getvalue()[tail_value]
                elif tail_name is Token.ELEM:
                    index = self.interpret_expression(tail_value).getvalue()
                    target = target.getvalue()[index]
                elif tail_name is Token.CALL:
                    args = (self.interpret_expression(arg).getvalue() for arg in tail_value)
                    target = Reference(target.getvalue()(*args))
            ref = target

        elif name is Token.ID:
            # XXX error handling (unknown id)
            ref = (self.this[expr[1]] if expr[1] in self.this else
                   self.global_vars[expr[1]])
        
        # literal
        elif name in token_keys:
            ref = Reference(expr[1])

        elif name is Token.ARRAY:
            array = []
            for key, elem in enumerate(expr[1]):
                value = self.interpret_expression(elem).getvalue()
                array.append(Reference(value, (array, key)))
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
            obj[f.group('key')] = self.build_function(argnames, Parser(f.group('code')).parse())

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

        return self.build_function(argnames, Parser(func_m.group('code')).parse())

    def push_context(self, cx):
        self._context_stack.append(self._context)
        self._context = cx

    def pop_context(self):
        # XXX check underflow
        self._context = self._context_stack.pop()

    def call_function(self, funcname, *args):
        f = (self.this[funcname] if funcname in self.this else
             self.global_vars[funcname] if funcname in self.global_vars else
             self.extract_function(funcname))
        return f(*args)

    def build_function(self, argnames, ast):
        def resf(*args):
            self.push_context(Context(dict(zip(argnames, args))))
            res = None
            for stmt in ast:
                res = self.interpret_statement(stmt)
                res = None if res is None else res.getvalue(deep=True)
                if self._context.ended:
                    self.pop_context()
                    break
            return res
        return resf

    def run(self, cx=None):
        if cx is not None:
            self.push_context(cx)
        res = None
        for stmt in Parser(self.code).parse():
            res = self.interpret_statement(stmt)
            res = None if res is None else res.getvalue(deep=True)
            if self._context.ended:
                if cx is not None:
                    self.pop_context()
                break
        return res
