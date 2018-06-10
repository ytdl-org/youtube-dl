from __future__ import unicode_literals

from youtube_dl.jsinterp2.jsgrammar import Token
from youtube_dl.jsinterp2.tstream import _OPERATORS

skip = {'jsinterp':  'Not yet fully implemented'}

tests = [
    {
        'code': '''
            function x() {
                var x = /* 1 + */ 2;
                var y = /* 30
                * 40 */ 50;
                return x + y;
            }
        ''',
        'asserts': [{'value': 52, 'call': ('x',)}],
        'ast': [
            (Token.FUNC, 'x', [], [
                (Token.VAR, zip(
                    ['x'],
                    [(Token.ASSIGN,
                      None,
                      (Token.OPEXPR, [(Token.MEMBER, (Token.INT, 2), None, None)]),
                      None)]
                )),
                (Token.VAR, zip(
                    ['y'],
                    [(Token.ASSIGN,
                      None,
                      (Token.OPEXPR, [(Token.MEMBER, (Token.INT, 50), None, None)]),
                      None)]
                )),
                (Token.RETURN, (Token.EXPR, [
                    (Token.ASSIGN, None,
                     (Token.OPEXPR, [
                         (Token.MEMBER, (Token.ID, 'x'), None, None),
                         (Token.MEMBER, (Token.ID, 'y'), None, None),
                         (Token.OP, _OPERATORS['+'][1])
                     ]), None)
                ]))
            ])
        ]
    }, {
        'code': '''
            function f() {
                var x = "/*";
                var y = 1 /* comment */ + 2;
                return y;
            }
        ''',
        'asserts': [{'value': 3, 'call': ('f',)}],
        'ast': [
            (Token.FUNC, 'f', [], [
                (Token.VAR, zip(
                    ['x'],
                    [(Token.ASSIGN,
                      None,
                      (Token.OPEXPR, [(Token.MEMBER, (Token.STR, '/*'), None, None)]),
                      None)]
                )),
                (Token.VAR, zip(
                    ['y'],
                    [(Token.ASSIGN,
                      None,
                      (Token.OPEXPR, [
                          (Token.MEMBER, (Token.INT, 1), None, None),
                          (Token.MEMBER, (Token.INT, 2), None, None),
                          (Token.OP, _OPERATORS['+'][1])
                      ]),
                      None)]
                )),
                (Token.RETURN, (Token.EXPR, [
                    (Token.ASSIGN, None,
                     (Token.OPEXPR, [(Token.MEMBER, (Token.ID, 'y'), None, None)]),
                     None)
                ]))
            ])
        ]
    }
]
