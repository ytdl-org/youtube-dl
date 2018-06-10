from __future__ import unicode_literals

from youtube_dl.jsinterp2.jsgrammar import TokenTypes
from youtube_dl.jsinterp2.tstream import _OPERATORS

tests = [
    {
        'code': 'function $_xY1 ($_axY1) { var $_axY2 = $_axY1 + 1; return $_axY2; }',
        'asserts': [{'value': 21, 'call': ('$_xY1', 20)}],
        'ast': [
            (TokenTypes.FUNC, '$_xY1', ['$_axY1'], [
                (TokenTypes.VAR,
                 zip(['$_axY2'],
                     [(TokenTypes.ASSIGN,
                       None,
                       (TokenTypes.OPEXPR, [
                           (TokenTypes.MEMBER, (TokenTypes.ID, '$_axY1'), None, None),
                           (TokenTypes.MEMBER, (TokenTypes.INT, 1), None, None),
                           (TokenTypes.OP, _OPERATORS['+'][1])
                       ]),
                       None)
                      ])
                 ),
                (TokenTypes.RETURN,
                 (TokenTypes.EXPR, [
                     (TokenTypes.ASSIGN,
                      None,
                      (TokenTypes.OPEXPR, [(TokenTypes.MEMBER, (TokenTypes.ID, '$_axY2'), None, None)]),
                      None)]
                  )
                 )
            ])
        ]
    }
]
