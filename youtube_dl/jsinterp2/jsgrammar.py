from __future__ import unicode_literals

import re

from collections import namedtuple

_token_keys = ('COPEN', 'CCLOSE', 'POPEN', 'PCLOSE', 'SOPEN', 'SCLOSE',
               'DOT', 'END', 'COMMA', 'HOOK', 'COLON',
               'AND', 'OR', 'PLUS', 'NEG', 'INC', 'DEC', 'NOT', 'BNOT', 'DEL', 'VOID', 'TYPE',
               'LT', 'GT', 'LE', 'GE', 'EQ', 'NE', 'SEQ', 'SNE', 'IN', 'INSTANCEOF',
               'BOR', 'BXOR', 'BAND', 'RSHIFT', 'LSHIFT', 'URSHIFT', 'SUB', 'ADD', 'MOD', 'DIV', 'MUL',
               'OP', 'AOP', 'UOP', 'LOP', 'REL', 'PREFIX', 'POSTFIX',
               'COMMENT', 'TOKEN', 'PUNCT',
               'NULL', 'BOOL', 'ID', 'STR', 'INT', 'FLOAT', 'REGEX', 'OBJECT',
               'REFLAGS', 'REBODY',
               'FUNC',
               'BLOCK', 'VAR', 'EXPR', 'IF', 'FOR', 'DO', 'WHILE', 'CONTINUE', 'BREAK', 'RETURN',
               'WITH', 'LABEL', 'SWITCH', 'THROW', 'TRY', 'DEBUG',
               'ASSIGN', 'MEMBER', 'FIELD', 'ELEM', 'CALL', 'ARRAY', 'COND', 'OPEXPR',
               'PROPGET', 'PROPSET', 'PROPVALUE',
               'RSV')

Token = namedtuple('Token', _token_keys)._make(_token_keys)

__DECIMAL_RE = r'(?:[1-9][0-9]*)|0'
__OCTAL_RE = r'0[0-7]+'
__HEXADECIMAL_RE = r'0[xX][0-9a-fA-F]+'
__ESC_UNICODE_RE = r'u[0-9a-fA-F]{4}'
__ESC_HEX_RE = r'x[0-9a-fA-F]{2}'


# NOTE order is fixed due to regex matching, does not represent any precedence
# NOTE unary operator 'delete', 'void', 'instanceof' and relation 'in' and 'instanceof' do not handled this way
_logical_operator = ['||', '&&']
_relation = ['===', '!==', '==', '!=', '<=', '>=', '<', '>']
_unary_operator = ['++', '--', '!', '~']
_operator = ['|', '^', '&', '>>>', '>>', '<<', '-', '+', '%', '/', '*']
_assign_operator = [op + '=' for op in _operator]
_assign_operator.append('=')
_punctuations = ['{', '}', '(', ')', '[', ']', '.', ';', ',', '?', ':']

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
_REGEX_FLAGS_RE = r'(?![gimy]*(?P<reflag>[gimy])[gimy]*(?P=reflag))(?P<%s>[gimy]{0,4}\b)' % 'REFLAGS'
_REGEX_RE = r'/(?!\*)(?P<%s>(?:[^/\n]|(?:\\/))*)/(?:(?:%s)|(?:\s|$))' % ('REBODY', _REGEX_FLAGS_RE)

token_keys = Token.NULL, Token.BOOL, Token.ID, Token.STR, Token.INT, Token.FLOAT, Token.REGEX

_TOKENS = zip(token_keys, (_NULL_RE, _BOOL_RE, _NAME_RE, _STRING_RE, _INTEGER_RE, _FLOAT_RE, _REGEX_RE))


COMMENT_RE = r'(?P<%s>/\*(?:(?!\*/)(?:\n|.))*\*/)' % Token.COMMENT
TOKENS_RE = r'|'.join('(?P<%(id)s>%(value)s)' % {'id': name, 'value': value}
                      for name, value in _TOKENS)

LOGICAL_OPERATORS_RE = r'(?P<%s>%s)' % (Token.LOP, r'|'.join(re.escape(value) for value in _logical_operator))
UNARY_OPERATORS_RE = r'(?P<%s>%s)' % (Token.UOP, r'|'.join(re.escape(value) for value in _unary_operator))
ASSIGN_OPERATORS_RE = r'(?P<%s>%s)' % (Token.AOP,
                                       r'|'.join(re.escape(value) if value != '=' else re.escape(value) + r'(?!\=)'
                                                 for value in _assign_operator))
OPERATORS_RE = r'(?P<%s>%s)' % (Token.OP, r'|'.join(re.escape(value) for value in _operator))
RELATIONS_RE = r'(?P<%s>%s)' % (Token.REL, r'|'.join(re.escape(value) for value in _relation))
PUNCTUATIONS_RE = r'(?P<%s>%s)' % (Token.PUNCT, r'|'.join(re.escape(value) for value in _punctuations))
