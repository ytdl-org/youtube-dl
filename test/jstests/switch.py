from __future__ import unicode_literals

from youtube_dl.jsinterp2.jsgrammar import TokenTypes
from youtube_dl.jsinterp2.tstream import _ASSIGN_OPERATORS, _UNARY_OPERATORS

skip = {
    'jsinterp': 'Switch statement is not supported',
    'interpret': 'Interpreting switch statement is not yet implemented'
}

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
            (TokenTypes.FUNC, 'a', ['x'], [
                (TokenTypes.SWITCH, (TokenTypes.EXPR, [(TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                    (TokenTypes.MEMBER, (TokenTypes.ID, 'x'), None, None)
                ]), None)]),
                 [
                     ((TokenTypes.EXPR, [(TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                         (TokenTypes.MEMBER, (TokenTypes.INT, 6), None, None)]), None)]),
                      [
                          (TokenTypes.BREAK, None)
                      ]),
                     ((TokenTypes.EXPR, [(TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                         (TokenTypes.MEMBER, (TokenTypes.INT, 5), None, None)]), None)]),
                      [
                          (TokenTypes.EXPR, [(TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                              (TokenTypes.MEMBER, (TokenTypes.ID, 'x'), None, None),
                              (TokenTypes.POSTFIX, _UNARY_OPERATORS['++'][1])
                          ]), None)])
                      ]),
                     ((TokenTypes.EXPR, [(TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                         (TokenTypes.MEMBER, (TokenTypes.INT, 8), None, None)]), None)]),
                      [
                          (TokenTypes.EXPR, [(TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                              (TokenTypes.MEMBER, (TokenTypes.ID, 'x'), None, None),
                              (TokenTypes.POSTFIX, _UNARY_OPERATORS['--'][1])
                          ]), None)]),
                          (TokenTypes.BREAK, None)
                      ]),
                     (None,
                      [
                          (TokenTypes.EXPR, [
                              (TokenTypes.ASSIGN,
                               _ASSIGN_OPERATORS['='][1],
                               (TokenTypes.OPEXPR, [(TokenTypes.MEMBER, (TokenTypes.ID, 'x'), None, None)]),
                               (TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [(TokenTypes.MEMBER, (TokenTypes.INT, 0), None, None)]), None)
                               )
                          ])
                      ])
                 ]
                 ),
                (TokenTypes.RETURN, (TokenTypes.EXPR, [(TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                    (TokenTypes.MEMBER, (TokenTypes.ID, 'x'), None, None)]), None)]))
            ])
        ]
    }
]
