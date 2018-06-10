from __future__ import unicode_literals

from youtube_dl.jsinterp2.jsgrammar import TokenTypes

tests = [
    {
        'code': 'function f() { return 42; }',
        'asserts': [{'value': 42, 'call': ('f',)}],
        'ast': [
            (TokenTypes.FUNC, 'f', [], [
                (TokenTypes.RETURN,
                 (TokenTypes.EXPR, [
                     (TokenTypes.ASSIGN,
                      None,
                      (TokenTypes.OPEXPR, [(TokenTypes.MEMBER, (TokenTypes.INT, 42), None, None)]),
                      None)
                 ]))
            ])
        ]
    },
    {
        'code': 'function x() {;}',
        'asserts': [{'value': None, 'call': ('x',)}],
        'ast': [(TokenTypes.FUNC, 'x', [], [None])]
    },
    {
        # FIXME: function expression needs to be implemented
        'exclude': ('jsinterp2',),
        'code': 'var x5 = function x5(){return 42;}',
        'asserts': [{'value': 42, 'call': ('x5',)}]
    }
]
