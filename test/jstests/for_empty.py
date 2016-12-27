from youtube_dl.jsinterp.jsgrammar import Token
from youtube_dl.jsinterp.tstream import _ASSIGN_OPERATORS, _UNARY_OPERATORS, _RELATIONS

skip = {'interpret': 'Interpreting for empty loop not yet implemented'}

tests = [
    {
        'code': '''
            function f(x){
                var h = 0;
                for (; h <= x; ++h) {
                    a = h;
                }
                return a;
            }
            ''',
        'asserts': [{'value': 5, 'call': ('f', 5)}],
        'ast': [
            (Token.FUNC, 'f', ['x'], [
                (Token.VAR, zip(['h'], [
                    (Token.ASSIGN, None, (Token.OPEXPR, [(Token.MEMBER, (Token.INT, 0), None, None)]), None)
                ])),
                (Token.FOR,
                 None,
                 (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                     (Token.MEMBER, (Token.ID, 'h'), None, None),
                     (Token.MEMBER, (Token.ID, 'x'), None, None),
                     (Token.REL, _RELATIONS['<='][1])
                 ]), None)]),
                 (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                     (Token.MEMBER, (Token.ID, 'h'), None, None),
                     (Token.PREFIX, _UNARY_OPERATORS['++'][1])
                 ]), None)]),
                 (Token.BLOCK, [
                     (Token.EXPR, [
                         (Token.ASSIGN, _ASSIGN_OPERATORS['='][1],
                          (Token.OPEXPR, [(Token.MEMBER, (Token.ID, 'a'), None, None)]),
                          (Token.ASSIGN, None, (Token.OPEXPR, [(Token.MEMBER, (Token.ID, 'h'), None, None)]), None))
                     ])
                 ])),
                (Token.RETURN, (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                    (Token.MEMBER, (Token.ID, 'a'), None, None)]), None)]))
            ])
        ]
    }
]
