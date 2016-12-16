from youtube_dl.jsinterp.jsgrammar import Token
from youtube_dl.jsinterp.tstream import _ASSIGN_OPERATORS

tests = [
    {
        'code': 'x =  2  ; return x;',
        'asserts': [{'value': 2}],
        'ast': [
            (Token.EXPR,
             [(Token.ASSIGN,
               _ASSIGN_OPERATORS['='][1],
               (Token.OPEXPR, [(Token.MEMBER, (Token.ID, 'x'), None, None)]),
               (Token.ASSIGN,
                None,
                (Token.OPEXPR, [(Token.MEMBER, (Token.INT, 2), None, None)]),
                None)
               )]
             ),
            (Token.RETURN,
             (Token.EXPR, [
                 (Token.ASSIGN,
                  None,
                  (Token.OPEXPR, [(Token.MEMBER, (Token.ID, 'x'), None, None)]),
                  None)
             ])
             )]
    }, {
        'code': 'function x (a) { return 2 * a + 1 ; }',
        'asserts': [{'value': 7, 'call': ('x', 3)}]
    }
]
