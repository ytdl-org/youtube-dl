from __future__ import unicode_literals

from youtube_dl.jsinterp2.jsgrammar import TokenTypes
from youtube_dl.jsinterp2.tstream import _ASSIGN_OPERATORS

tests = [
    {
        'code': 'function f() { x =  2  ; return x; }',
        'asserts': [{'value': 2, 'call': ('f',)}],
        'ast': [
            (TokenTypes.FUNC, 'f', [], [
                (TokenTypes.EXPR,
                 [(TokenTypes.ASSIGN,
                   _ASSIGN_OPERATORS['='][1],
                   (TokenTypes.OPEXPR, [(TokenTypes.MEMBER, (TokenTypes.ID, 'x'), None, None)]),
                   (TokenTypes.ASSIGN,
                    None,
                    (TokenTypes.OPEXPR, [(TokenTypes.MEMBER, (TokenTypes.INT, 2), None, None)]),
                    None)
                   )]
                 ),
                (TokenTypes.RETURN,
                 (TokenTypes.EXPR, [
                     (TokenTypes.ASSIGN,
                      None,
                      (TokenTypes.OPEXPR, [(TokenTypes.MEMBER, (TokenTypes.ID, 'x'), None, None)]),
                      None)
                 ])
                 )
            ])
        ]
    }, {
        'code': 'function x (a) { return 2 * a + 1 ; }',
        'asserts': [{'value': 7, 'call': ('x', 3)}]
    }
]
