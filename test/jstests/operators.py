from __future__ import unicode_literals

from youtube_dl.jsinterp2.jsgrammar import Token
from youtube_dl.jsinterp2.tstream import _OPERATORS

tests = [
    {
        'code': 'function f() { return 1 << 5; }',
        'asserts': [{'value': 32, 'call': ('f',)}],
        'ast': [
            (Token.FUNC, 'f', [], [
                (Token.RETURN,
                 (Token.EXPR, [
                     (Token.ASSIGN, None, (Token.OPEXPR, [
                         (Token.MEMBER, (Token.INT, 1), None, None),
                         (Token.MEMBER, (Token.INT, 5), None, None),
                         (Token.OP, _OPERATORS['<<'][1])
                     ]), None)
                 ]))
            ])
        ]
    }, {
        'code': 'function f() { return 19 & 21;}',
        'asserts': [{'value': 17, 'call': ('f',)}],
        'ast': [
            (Token.FUNC, 'f', [], [
                (Token.RETURN,
                 (Token.EXPR, [
                     (Token.ASSIGN, None, (Token.OPEXPR, [
                         (Token.MEMBER, (Token.INT, 19), None, None),
                         (Token.MEMBER, (Token.INT, 21), None, None),
                         (Token.OP, _OPERATORS['&'][1])
                     ]), None)
                 ]))
            ])
        ]
    }, {
        'code': 'function f() { return 11 >> 2;}',
        'asserts': [{'value': 2, 'call': ('f',)}],
        'ast': [
            (Token.FUNC, 'f', [], [
                (Token.RETURN,
                 (Token.EXPR, [
                     (Token.ASSIGN, None, (Token.OPEXPR, [
                         (Token.MEMBER, (Token.INT, 11), None, None),
                         (Token.MEMBER, (Token.INT, 2), None, None),
                         (Token.OP, _OPERATORS['>>'][1])
                     ]), None)
                 ]))
            ])
        ]
    }
]
