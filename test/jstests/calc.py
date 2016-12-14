from youtube_dl.jsinterp.jsgrammar import Token
from youtube_dl.jsinterp.tstream import _OPERATORS

tests = [
    {'code': 'return 2*a+1;',
     'globals': {'a': 3},
     'asserts': [{'value': 7}],
     'ast': [(Token.RETURN,
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
              )]
     }
]
