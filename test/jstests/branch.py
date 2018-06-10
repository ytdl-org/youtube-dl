from __future__ import unicode_literals

from youtube_dl.jsinterp2.jsgrammar import TokenTypes
from youtube_dl.jsinterp2.tstream import _RELATIONS

skip = {
    'jsinterp': 'Branching is not supported',
    'interpret': 'Interpreting if statement not yet implemented'
}

tests = [
    {
        'code': '''
            function a(x) {
                if (x > 0)
                    return true;
                else
                    return false;
            }
            ''',
        'asserts': [{'value': True, 'call': ('a', 1)}, {'value': False, 'call': ('a', 0)}],
        'ast': [
            (TokenTypes.FUNC, 'a', ['x'], [
                (TokenTypes.IF,
                 (TokenTypes.EXPR, [(TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                     (TokenTypes.MEMBER, (TokenTypes.ID, 'x'), None, None),
                     (TokenTypes.MEMBER, (TokenTypes.INT, 0), None, None),
                     (TokenTypes.REL, _RELATIONS['>'][1])
                 ]), None)]),
                 (TokenTypes.RETURN, (TokenTypes.EXPR, [(TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                     (TokenTypes.MEMBER, (TokenTypes.BOOL, True), None, None)]), None)])),
                 (TokenTypes.RETURN, (TokenTypes.EXPR, [(TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                     (TokenTypes.MEMBER, (TokenTypes.BOOL, False), None, None)]), None)])))
            ])
        ]
    }
]
