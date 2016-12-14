from youtube_dl.jsinterp.jsgrammar import Token
from youtube_dl.jsinterp.tstream import _OPERATORS

tests = [
    {
        'code': 'var $_axY2 = $_xY1 + 1; return $_axY2;',
        'globals': {'$_xY1': 20},
        'asserts': [{'value': 21}],
        'ast': [
            (Token.VAR,
             zip(['$_axY2'],
                 [(Token.ASSIGN,
                   None,
                   (Token.OPEXPR, [
                       (Token.MEMBER, (Token.ID, '$_xY1'), None, None),
                       (Token.MEMBER, (Token.INT, 1), None, None),
                       (Token.OP, _OPERATORS['+'][1])
                   ]),
                   None)
                  ])
             ),
            (Token.RETURN,
             (Token.EXPR, [
                 (Token.ASSIGN,
                  None,
                  (Token.OPEXPR, [(Token.MEMBER, (Token.ID, '$_axY2'), None, None)]),
                  None)]
              )
             )]
    }
]
