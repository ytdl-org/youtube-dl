from __future__ import unicode_literals

from youtube_dl.jsinterp2.jsgrammar import TokenTypes
from youtube_dl.jsinterp2.tstream import _OPERATORS, _ASSIGN_OPERATORS

tests = [
    {
        'code': 'function f() { var x = 20; x = 30 + 1; return x; }',
        'asserts': [{'value': 31, 'call': ('f',)}],
        'ast': [
            (TokenTypes.FUNC, 'f', [], [
                (TokenTypes.VAR, zip(
                    ['x'],
                    [(TokenTypes.ASSIGN,
                      None,
                      (TokenTypes.OPEXPR, [(TokenTypes.MEMBER, (TokenTypes.INT, 20), None, None)]),
                      None)]
                )),
                (TokenTypes.EXPR, [
                    (TokenTypes.ASSIGN,
                     _ASSIGN_OPERATORS['='][1],
                     (TokenTypes.OPEXPR, [(TokenTypes.MEMBER, (TokenTypes.ID, 'x'), None, None)]),
                     (TokenTypes.ASSIGN, None,
                      (TokenTypes.OPEXPR, [
                          (TokenTypes.MEMBER, (TokenTypes.INT, 30), None, None),
                          (TokenTypes.MEMBER, (TokenTypes.INT, 1), None, None),
                          (TokenTypes.OP, _OPERATORS['+'][1])]),
                      None))
                ]),

                (TokenTypes.RETURN, (TokenTypes.EXPR, [
                    (TokenTypes.ASSIGN, None,
                     (TokenTypes.OPEXPR, [
                         (TokenTypes.MEMBER, (TokenTypes.ID, 'x'), None, None)
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
