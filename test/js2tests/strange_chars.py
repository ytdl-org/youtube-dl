from __future__ import unicode_literals

from youtube_dl.jsinterp2.jsgrammar import Token
from youtube_dl.jsinterp2.tstream import _OPERATORS

tests = [
    {
        'code': 'function $_xY1 ($_axY1) { var $_axY2 = $_axY1 + 1; return $_axY2; }',
        'asserts': [{'value': 21, 'call': ('$_xY1', 20)}],
        'ast': [
            (Token.FUNC, '$_xY1', ['$_axY1'], [
                (Token.VAR,
                 zip(['$_axY2'],
                     [(Token.ASSIGN,
                       None,
                       (Token.OPEXPR, [
                           (Token.MEMBER, (Token.ID, '$_axY1'), None, None),
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
                 )
            ])
        ]
    }
]
