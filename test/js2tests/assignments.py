from __future__ import unicode_literals

from youtube_dl.jsinterp2.jsgrammar import Token
from youtube_dl.jsinterp2.tstream import _OPERATORS, _ASSIGN_OPERATORS

tests = [
    {
        'code': 'function f() { var x = 20; x = 30 + 1; return x; }',
        'asserts': [{'value': 31, 'call': ('f',)}],
        'ast': [
            (Token.FUNC, 'f', [], [
                (Token.VAR, zip(
                    ['x'],
                    [(Token.ASSIGN,
                      None,
                      (Token.OPEXPR, [(Token.MEMBER, (Token.INT, 20), None, None)]),
                      None)]
                )),
                (Token.EXPR, [
                    (Token.ASSIGN,
                     _ASSIGN_OPERATORS['='][1],
                     (Token.OPEXPR, [(Token.MEMBER, (Token.ID, 'x'), None, None)]),
                     (Token.ASSIGN, None,
                      (Token.OPEXPR, [
                          (Token.MEMBER, (Token.INT, 30), None, None),
                          (Token.MEMBER, (Token.INT, 1), None, None),
                          (Token.OP, _OPERATORS['+'][1])]),
                      None))
                ]),

                (Token.RETURN, (Token.EXPR, [
                    (Token.ASSIGN, None,
                     (Token.OPEXPR, [
                         (Token.MEMBER, (Token.ID, 'x'), None, None)
                     ]), None)
                ]))
            ])
        ]
    }, {
        'code': 'function f() { var x = 20; x += 30 + 1; return x;}',
        'asserts': [{'value': 51, 'call': ('f',)}],
    }, {
        'code': 'function f() { var x = 20; x -= 30 + 1; return x;}',
        'asserts': [{'value': -11, 'call': ('f',)}],
    }
]
