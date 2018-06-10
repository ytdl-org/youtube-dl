from __future__ import unicode_literals

from youtube_dl.jsinterp2.jsgrammar import TokenTypes
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
            (TokenTypes.FUNC, 'x', [], [
                (TokenTypes.VAR, zip(
                    ['x'],
                    [(TokenTypes.ASSIGN,
                      None,
                      (TokenTypes.OPEXPR, [(TokenTypes.MEMBER, (TokenTypes.INT, 2), None, None)]),
                      None)]
                )),
                (TokenTypes.VAR, zip(
                    ['y'],
                    [(TokenTypes.ASSIGN,
                      None,
                      (TokenTypes.OPEXPR, [(TokenTypes.MEMBER, (TokenTypes.INT, 50), None, None)]),
                      None)]
                )),
                (TokenTypes.RETURN, (TokenTypes.EXPR, [
                    (TokenTypes.ASSIGN, None,
                     (TokenTypes.OPEXPR, [
                         (TokenTypes.MEMBER, (TokenTypes.ID, 'x'), None, None),
                         (TokenTypes.MEMBER, (TokenTypes.ID, 'y'), None, None),
                         (TokenTypes.OP, _OPERATORS['+'][1])
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
            (TokenTypes.FUNC, 'f', [], [
                (TokenTypes.VAR, zip(
                    ['x'],
                    [(TokenTypes.ASSIGN,
                      None,
                      (TokenTypes.OPEXPR, [(TokenTypes.MEMBER, (TokenTypes.STR, '/*'), None, None)]),
                      None)]
                )),
                (TokenTypes.VAR, zip(
                    ['y'],
                    [(TokenTypes.ASSIGN,
                      None,
                      (TokenTypes.OPEXPR, [
                          (TokenTypes.MEMBER, (TokenTypes.INT, 1), None, None),
                          (TokenTypes.MEMBER, (TokenTypes.INT, 2), None, None),
                          (TokenTypes.OP, _OPERATORS['+'][1])
                      ]),
                      None)]
                )),
                (TokenTypes.RETURN, (TokenTypes.EXPR, [
                    (TokenTypes.ASSIGN, None,
                     (TokenTypes.OPEXPR, [(TokenTypes.MEMBER, (TokenTypes.ID, 'y'), None, None)]),
                     None)
                ]))
            ])
        ]
    }
]
