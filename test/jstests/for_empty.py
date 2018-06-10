from __future__ import unicode_literals

from youtube_dl.jsinterp2.jsgrammar import TokenTypes
from youtube_dl.jsinterp2.tstream import _ASSIGN_OPERATORS, _UNARY_OPERATORS, _RELATIONS

skip = {
    'jsinterp': 'For loop is not supported',
    'interpret': 'Interpreting for empty loop is not yet implemented'
}

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
            (TokenTypes.FUNC, 'f', ['x'], [
                (TokenTypes.VAR, zip(['h'], [
                    (TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [(TokenTypes.MEMBER, (TokenTypes.INT, 0), None, None)]), None)
                ])),
                (TokenTypes.FOR,
                 None,
                 (TokenTypes.EXPR, [(TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                     (TokenTypes.MEMBER, (TokenTypes.ID, 'h'), None, None),
                     (TokenTypes.MEMBER, (TokenTypes.ID, 'x'), None, None),
                     (TokenTypes.REL, _RELATIONS['<='][1])
                 ]), None)]),
                 (TokenTypes.EXPR, [(TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                     (TokenTypes.MEMBER, (TokenTypes.ID, 'h'), None, None),
                     (TokenTypes.PREFIX, _UNARY_OPERATORS['++'][1])
                 ]), None)]),
                 (TokenTypes.BLOCK, [
                     (TokenTypes.EXPR, [
                         (TokenTypes.ASSIGN, _ASSIGN_OPERATORS['='][1],
                          (TokenTypes.OPEXPR, [(TokenTypes.MEMBER, (TokenTypes.ID, 'a'), None, None)]),
                          (TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [(TokenTypes.MEMBER, (TokenTypes.ID, 'h'), None, None)]), None))
                     ])
                 ])),
                (TokenTypes.RETURN, (TokenTypes.EXPR, [(TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                    (TokenTypes.MEMBER, (TokenTypes.ID, 'a'), None, None)]), None)]))
            ])
        ]
    }
]
