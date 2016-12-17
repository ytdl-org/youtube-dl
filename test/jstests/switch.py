from youtube_dl.jsinterp.jsgrammar import Token
from youtube_dl.jsinterp.tstream import _ASSIGN_OPERATORS, _UNARY_OPERATORS

skip = {'i': 'Interpreting switch statement not yet implemented'}

tests = [
    {
        'code': '''
            function a(x) {
                switch (x) {
                    case 6:
                        break;
                    case 5:
                        x++;
                    case 8:
                        x--;
                        break;
                    default:
                        x = 0;
                }
                return x;
            }
            ''',
        'asserts': [{'value': 4, 'call': ('a', 0)},
                    {'value': 5, 'call': ('a', 5)},
                    {'value': 6, 'call': ('a', 6)},
                    {'value': 8, 'call': ('a', 7)}],
        'ast': [
            (Token.FUNC, 'a', ['x'], [
                (Token.SWITCH, (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                    (Token.MEMBER, (Token.ID, 'x'), None, None)
                ]), None)]),
                 [
                     ((Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                         (Token.MEMBER, (Token.INT, 6), None, None)]), None)]),
                      [
                          (Token.BREAK, None)
                      ]),
                     ((Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                         (Token.MEMBER, (Token.INT, 5), None, None)]), None)]),
                      [
                          (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                              (Token.MEMBER, (Token.ID, 'x'), None, None),
                              (Token.POSTFIX, _UNARY_OPERATORS['++'][1])
                          ]), None)])
                      ]),
                     ((Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                         (Token.MEMBER, (Token.INT, 8), None, None)]), None)]),
                      [
                          (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                              (Token.MEMBER, (Token.ID, 'x'), None, None),
                              (Token.POSTFIX, _UNARY_OPERATORS['--'][1])
                          ]), None)]),
                          (Token.BREAK, None)
                      ]),
                     (None,
                      [
                          (Token.EXPR, [
                              (Token.ASSIGN,
                               _ASSIGN_OPERATORS['='][1],
                               (Token.OPEXPR, [(Token.MEMBER, (Token.ID, 'x'), None, None)]),
                               (Token.ASSIGN, None, (Token.OPEXPR, [(Token.MEMBER, (Token.INT, 0), None, None)]), None)
                               )
                          ])
                      ])
                 ]
                 ),
                (Token.RETURN, (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                    (Token.MEMBER, (Token.ID, 'x'), None, None)]), None)]))
            ])
        ]
    }
]
