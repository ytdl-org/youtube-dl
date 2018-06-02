from __future__ import unicode_literals

from youtube_dl.jsinterp2.jsgrammar import Token

skip = {'jsinterp': 'Field access is not supported'}

tests = [
    {
        'code': 'function f() { return a.var; }',
        'asserts': [{'value': 3, 'call': ('f',)}],
        'globals': {'a': {'var': 3}},
        'ast': [
            (Token.FUNC, 'f', [], [
                (Token.RETURN,
                 (Token.EXPR, [
                     (Token.ASSIGN,
                      None,
                      (Token.OPEXPR, [
                          (Token.MEMBER,
                           (Token.ID, 'a'),
                           None,
                           (Token.FIELD, 'var', None)),
                      ]),
                      None)
                 ]))
            ])
        ]
    }
]
