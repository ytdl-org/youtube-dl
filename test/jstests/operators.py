from __future__ import unicode_literals

from youtube_dl.jsinterp2.jsgrammar import TokenTypes
from youtube_dl.jsinterp2.tstream import _OPERATORS

tests = [
    {
        'code': 'function f() { return 1 << 5; }',
        'asserts': [{'value': 32, 'call': ('f',)}],
        'ast': [
            (TokenTypes.FUNC, 'f', [], [
                (TokenTypes.RETURN,
                 (TokenTypes.EXPR, [
                     (TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                         (TokenTypes.MEMBER, (TokenTypes.INT, 1), None, None),
                         (TokenTypes.MEMBER, (TokenTypes.INT, 5), None, None),
                         (TokenTypes.OP, _OPERATORS['<<'][1])
                     ]), None)
                 ]))
            ])
        ]
    }, {
        'code': 'function f() { return 19 & 21;}',
        'asserts': [{'value': 17, 'call': ('f',)}],
        'ast': [
            (TokenTypes.FUNC, 'f', [], [
                (TokenTypes.RETURN,
                 (TokenTypes.EXPR, [
                     (TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                         (TokenTypes.MEMBER, (TokenTypes.INT, 19), None, None),
                         (TokenTypes.MEMBER, (TokenTypes.INT, 21), None, None),
                         (TokenTypes.OP, _OPERATORS['&'][1])
                     ]), None)
                 ]))
            ])
        ]
    }, {
        'code': 'function f() { return 11 >> 2;}',
        'asserts': [{'value': 2, 'call': ('f',)}],
        'ast': [
            (TokenTypes.FUNC, 'f', [], [
                (TokenTypes.RETURN,
                 (TokenTypes.EXPR, [
                     (TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                         (TokenTypes.MEMBER, (TokenTypes.INT, 11), None, None),
                         (TokenTypes.MEMBER, (TokenTypes.INT, 2), None, None),
                         (TokenTypes.OP, _OPERATORS['>>'][1])
                     ]), None)
                 ]))
            ])
        ]
    }
]
