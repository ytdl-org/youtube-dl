from __future__ import unicode_literals

from youtube_dl.jsinterp2.jsgrammar import Token
from youtube_dl.jsinterp2.tstream import _OPERATORS

tests = [
    {'code': 'function x4(a){return 2*a+1;}',
     'asserts': [{'value': 7, 'call': ('x4', 3)}],
     'ast': [
         (Token.FUNC, 'x4', ['a'], [
            (Token.RETURN,
              (Token.EXPR, [
                  (Token.ASSIGN,
                   None,
                   (Token.OPEXPR, [
                       # Reverse Polish Notation!
                       (Token.MEMBER, (Token.INT, 2), None, None),
                       (Token.MEMBER, (Token.ID, 'a'), None, None),
                       (Token.OP, _OPERATORS['*'][1]),
                       (Token.MEMBER, (Token.INT, 1), None, None),
                       (Token.OP, _OPERATORS['+'][1])
                   ]),
                   None)
              ])
              )
         ])
     ]
     }
]
