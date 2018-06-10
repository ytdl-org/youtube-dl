from __future__ import unicode_literals

from youtube_dl.jsinterp2.jsgrammar import TokenTypes
from youtube_dl.jsinterp2.tstream import _ASSIGN_OPERATORS

skip = {
    'jsinterp': 'For in loop is not supported',
    'interpret': 'Interpreting for in loop is not yet implemented'
}

tests = [
    {
        'code': '''
            function f(z){
                    for (h in z) {
                        a = h;
                    }
                    return a;
                }
                ''',
        'asserts': [{'value': 'c', 'call': ('f', ['a', 'b', 'c'])}],
        'ast': [
            (TokenTypes.FUNC, 'f', ['z'], [
                (TokenTypes.FOR,
                 (TokenTypes.EXPR, [(TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                     (TokenTypes.MEMBER, (TokenTypes.ID, 'h'), None, None)
                 ]), None)]),
                 (TokenTypes.EXPR, [(TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                     (TokenTypes.MEMBER, (TokenTypes.ID, 'z'), None, None)
                 ]), None)]),
                 None,
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
