from __future__ import unicode_literals

from youtube_dl.jsinterp2.jsgrammar import TokenTypes
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
            (TokenTypes.FUNC, 'x', [], [
                (TokenTypes.RETURN, (TokenTypes.EXPR, [
                    (TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [(TokenTypes.MEMBER, (TokenTypes.INT, 2), None, None)]), None)
                ]))
            ]),
            (TokenTypes.FUNC, 'y', ['a'], [
                (TokenTypes.RETURN, (TokenTypes.EXPR, [
                    (TokenTypes.ASSIGN, None,
                     (TokenTypes.OPEXPR, [
                         (TokenTypes.MEMBER, (TokenTypes.ID, 'x'), None, (TokenTypes.CALL, [], None)),
                         (TokenTypes.MEMBER, (TokenTypes.ID, 'a'), None, None),
                         (TokenTypes.OP, _OPERATORS['+'][1])
                     ]), None)
                ]))
            ]),
            (TokenTypes.FUNC, 'z', [], [
                (TokenTypes.RETURN, (TokenTypes.EXPR, [
                    (TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                        (TokenTypes.MEMBER, (TokenTypes.ID, 'y'), None, (TokenTypes.CALL, [
                            (TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [(TokenTypes.MEMBER, (TokenTypes.INT, 3), None, None)]), None)
                        ], None))
                    ]), None)
                ])
                 )
            ])
        ]
    }, {
        'code': 'function x(a) { return a.split(""); }',
        'asserts': [{'value': ["a", "b", "c"], 'call': ('x', "abc")}],
        'ast': [
            (TokenTypes.FUNC, 'x', ['a'], [
                (TokenTypes.RETURN, (TokenTypes.EXPR, [
                    (TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                        (TokenTypes.MEMBER, (TokenTypes.ID, 'a'), None,
                         (TokenTypes.FIELD, 'split',
                          (TokenTypes.CALL, [
                              (TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [(TokenTypes.MEMBER, (TokenTypes.STR, ''), None, None)]), None)
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
            (TokenTypes.FUNC, 'a', ['x'], [
                (TokenTypes.RETURN, (TokenTypes.EXPR, [
                    (TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [(TokenTypes.MEMBER, (TokenTypes.ID, 'x'), None, None)]), None)
                ]))
            ]),
            (TokenTypes.FUNC, 'b', ['x'], [
                (TokenTypes.RETURN, (TokenTypes.EXPR, [
                    (TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                        (TokenTypes.MEMBER, (TokenTypes.ID, 'x'), None, None),
                        (TokenTypes.MEMBER, (TokenTypes.INT, 1), None, None),
                        (TokenTypes.OP, _OPERATORS['+'][1])
                    ]), None)
                ]))
            ]),
            (TokenTypes.FUNC, 'c', [], [
                (TokenTypes.RETURN, (TokenTypes.EXPR, [
                    (TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                        (TokenTypes.MEMBER, (TokenTypes.ARRAY, [
                            (TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                                (TokenTypes.MEMBER, (TokenTypes.ID, 'a'), None, None)]), None),
                            (TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                                (TokenTypes.MEMBER, (TokenTypes.ID, 'b'), None, None)]), None)
                        ]), None, (TokenTypes.ELEM, (TokenTypes.EXPR, [
                            (TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [(TokenTypes.MEMBER, (TokenTypes.INT, 0), None, None)]), None)
                        ]), (TokenTypes.CALL, [
                            (TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [(TokenTypes.MEMBER, (TokenTypes.INT, 0), None, None)]), None)
                        ], None)))
                    ]), None)
                ]))
            ])
        ]
    }
]
