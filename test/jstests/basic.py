from __future__ import unicode_literals

from youtube_dl.jsinterp2.jsgrammar import Token

tests = [
    {
        'code': 'function f() { return 42; }',
        'asserts': [{'value': 42, 'call': ('f',)}],
        'ast': [
            (Token.FUNC, 'f', [], [
                (Token.RETURN,
                 (Token.EXPR, [
                     (Token.ASSIGN,
                      None,
                      (Token.OPEXPR, [(Token.MEMBER, (Token.INT, 42), None, None)]),
                      None)
                 ]))
            ])
        ]
    },
    {
        'code': 'function x() {;}',
        'asserts': [{'value': None, 'call': ('x',)}],
        'ast': [(Token.FUNC, 'x', [], [None])]
    },
    {
        # FIXME: function expression needs to be implemented
        'exclude': ('jsinterp2',),
        'code': 'var x5 = function x5(){return 42;}',
        'asserts': [{'value': 42, 'call': ('x5',)}]
    }
]
