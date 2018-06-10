from __future__ import unicode_literals

from youtube_dl.jsinterp2.jsgrammar import TokenTypes
from youtube_dl.jsinterp2.tstream import _OPERATORS

tests = [
    {'code': 'function x4(a){return 2*a+1;}',
     'asserts': [{'value': 7, 'call': ('x4', 3)}],
     'ast': [
         (TokenTypes.FUNC, 'x4', ['a'], [
            (TokenTypes.RETURN,
             (TokenTypes.EXPR, [
                  (TokenTypes.ASSIGN,
                   None,
                   (TokenTypes.OPEXPR, [
                       # Reverse Polish Notation!
                       (TokenTypes.MEMBER, (TokenTypes.INT, 2), None, None),
                       (TokenTypes.MEMBER, (TokenTypes.ID, 'a'), None, None),
                       (TokenTypes.OP, _OPERATORS['*'][1]),
                       (TokenTypes.MEMBER, (TokenTypes.INT, 1), None, None),
                       (TokenTypes.OP, _OPERATORS['+'][1])
                   ]),
                   None)
             ])
             )
         ])
     ]
     }
]
