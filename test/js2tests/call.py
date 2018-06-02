from __future__ import unicode_literals

from youtube_dl.jsinterp2.jsgrammar import Token
from youtube_dl.jsinterp2.tstream import _OPERATORS

tests = [
    {
        'code': '''
            function x() { return 2; }
            function y(a) { return x() + a; }
            function z() { return y(3); }
            ''',
        'asserts': [{'value': 5, 'call': ('z',)}],
        'ast': [
            (Token.FUNC, 'x', [], [
                (Token.RETURN, (Token.EXPR, [
                    (Token.ASSIGN, None, (Token.OPEXPR, [(Token.MEMBER, (Token.INT, 2), None, None)]), None)
                ]))
            ]),
            (Token.FUNC, 'y', ['a'], [
                (Token.RETURN, (Token.EXPR, [
                    (Token.ASSIGN, None,
                     (Token.OPEXPR, [
                         (Token.MEMBER, (Token.ID, 'x'), None, (Token.CALL, [], None)),
                         (Token.MEMBER, (Token.ID, 'a'), None, None),
                         (Token.OP, _OPERATORS['+'][1])
                     ]), None)
                ]))
            ]),
            (Token.FUNC, 'z', [], [
                (Token.RETURN, (Token.EXPR, [
                    (Token.ASSIGN, None, (Token.OPEXPR, [
                        (Token.MEMBER, (Token.ID, 'y'), None, (Token.CALL, [
                            (Token.ASSIGN, None, (Token.OPEXPR, [(Token.MEMBER, (Token.INT, 3), None, None)]), None)
                        ], None))
                    ]), None)
                ])
                 )
            ])
        ]
    }, {
        # FIXME built-in functions not yet implemented
        'exclude': ('jsinterp2',),
        'code': 'function x(a) { return a.split(""); }',
        'asserts': [{'value': ["a", "b", "c"], 'call': ('x',"abc")}],
        'ast': [
            (Token.FUNC, 'x', ['a'], [
                (Token.RETURN, (Token.EXPR, [
                    (Token.ASSIGN, None, (Token.OPEXPR, [
                        (Token.MEMBER, (Token.ID, 'a'), None,
                         (Token.FIELD, 'split',
                          (Token.CALL, [
                              (Token.ASSIGN, None, (Token.OPEXPR, [(Token.MEMBER, (Token.STR, ''), None, None)]), None)
                          ], None))
                         )]),
                     None)
                ]))
            ])
        ]
    }, {
        'exclude': ('jsinterp',),
        'code': '''
            function a(x) { return x; }
            function b(x) { return x + 1; }
            function c()  { return [a, b][0](0); }
            ''',
        'asserts': [{'value': 0, 'call': ('c',)}],
        'ast': [
            (Token.FUNC, 'a', ['x'], [
                (Token.RETURN, (Token.EXPR, [
                    (Token.ASSIGN, None, (Token.OPEXPR, [(Token.MEMBER, (Token.ID, 'x'), None, None)]), None)
                ]))
            ]),
            (Token.FUNC, 'b', ['x'], [
                (Token.RETURN, (Token.EXPR, [
                    (Token.ASSIGN, None, (Token.OPEXPR, [
                        (Token.MEMBER, (Token.ID, 'x'), None, None),
                        (Token.MEMBER, (Token.INT, 1), None, None),
                        (Token.OP, _OPERATORS['+'][1])
                    ]), None)
                ]))
            ]),
            (Token.FUNC, 'c', [], [
                (Token.RETURN, (Token.EXPR, [
                    (Token.ASSIGN, None, (Token.OPEXPR, [
                        (Token.MEMBER, (Token.ARRAY, [
                            (Token.ASSIGN, None, (Token.OPEXPR, [
                                (Token.MEMBER, (Token.ID, 'a'), None, None)]), None),
                            (Token.ASSIGN, None, (Token.OPEXPR, [
                                (Token.MEMBER, (Token.ID, 'b'), None, None)]), None)
                        ]), None, (Token.ELEM, (Token.EXPR, [
                            (Token.ASSIGN, None, (Token.OPEXPR, [(Token.MEMBER, (Token.INT, 0), None, None)]), None)
                        ]), (Token.CALL, [
                            (Token.ASSIGN, None, (Token.OPEXPR, [(Token.MEMBER, (Token.INT, 0), None, None)]), None)
                        ], None)))
                    ]), None)
                ]))
            ])
        ]
    }
]
