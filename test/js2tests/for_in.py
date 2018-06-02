from __future__ import unicode_literals

from youtube_dl.jsinterp2.jsgrammar import Token
from youtube_dl.jsinterp2.tstream import _ASSIGN_OPERATORS

skip = {
    'jsinterp': 'For in loop is not supported',
    'interpret': 'Interpreting for in loop not yet implemented'
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
            (Token.FUNC, 'f', ['z'], [
                (Token.FOR,
                 (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                     (Token.MEMBER, (Token.ID, 'h'), None, None)
                 ]), None)]),
                 (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                     (Token.MEMBER, (Token.ID, 'z'), None, None)
                 ]), None)]),
                 None,
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
