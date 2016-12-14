from youtube_dl.jsinterp.jsgrammar import Token
from youtube_dl.jsinterp.tstream import _OPERATORS

skip = {'i': 'Interpreting function call not yet implemented'}

tests = [
    {
        'code': '''
            function x() { return 2; }
            function y(a) { return x() + a; }
            function z() { return y(3); }
            ''',
        'asserts': [{'value': 5, 'call': ('z',)}],
        'ast': [
            (Token.FUNC, 'x',
             [],
             (Token.BLOCK, [
                 (Token.RETURN, (Token.EXPR, [
                     (Token.ASSIGN, None, (Token.OPEXPR, [(Token.MEMBER, (Token.INT, 2), None, None)]), None)
                 ])
                  )
             ])),
            (Token.FUNC, 'y',
             ['a'],
             (Token.BLOCK, [
                 (Token.RETURN, (Token.EXPR, [
                     (Token.ASSIGN, None,
                      (Token.OPEXPR, [
                          (Token.MEMBER, (Token.ID, 'x'), None, (Token.CALL, [], None)),
                          (Token.MEMBER, (Token.ID, 'a'), None, None),
                          (Token.OP, _OPERATORS['+'][1])
                      ]), None)
                 ])
                  )
             ])),
            (Token.FUNC, 'z',
             [],
             (Token.BLOCK, [
                 (Token.RETURN, (Token.EXPR, [
                     (Token.ASSIGN, None, (Token.OPEXPR, [
                         (Token.MEMBER, (Token.ID, 'y'), None, (Token.CALL, [
                             (Token.ASSIGN, None, (Token.OPEXPR, [(Token.MEMBER, (Token.INT, 3), None, None)]), None)
                         ], None))
                     ]), None)
                 ])
                  )
             ]))
        ]
    }, {
        'code': 'function x(a) { return a.split(""); }',
        'asserts': [{'value': ["a", "b", "c"], 'call': ('x',)}],
        'ast': [
            (Token.FUNC, 'x',
             ['a'],
             (Token.BLOCK, [
                 (Token.RETURN, (Token.EXPR, [
                     (Token.ASSIGN, None, (Token.OPEXPR, [
                         (Token.MEMBER, (Token.ID, 'a'), None,
                          (Token.FIELD, 'split',
                           (Token.CALL, [
                               (Token.ASSIGN, None, (Token.OPEXPR, [(Token.MEMBER, (Token.STR, ''), None, None)]), None)
                           ], None))
                          )]),
                      None)
                 ])
                  )
             ]))
        ]
    }, {
        'code': '''
            function a(x) { return x; }
            function b(x) { return x; }
            function c()  { return [a, b][0](0); }
            ''',
        'asserts': [{'value': 0}],
        'ast': [
            (Token.FUNC, 'a', ['x'],
             (Token.BLOCK, [
                 (Token.RETURN, (Token.EXPR, [
                     (Token.ASSIGN, None, (Token.OPEXPR, [(Token.MEMBER, (Token.ID, 'x'), None, None)]), None)
                 ])
                  )
             ])),
            (Token.FUNC, 'b', ['x'],
             (Token.BLOCK, [
                 (Token.RETURN, (Token.EXPR, [
                     (Token.ASSIGN, None, (Token.OPEXPR, [(Token.MEMBER, (Token.ID, 'x'), None, None)]), None)
                 ])
                  )
             ])),
            (Token.FUNC, 'c', [],
             (Token.BLOCK, [
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
                 ])
                  )
             ]))
        ]
    }
]
