from __future__ import unicode_literals

from youtube_dl.jsinterp2.jsgrammar import TokenTypes

skip = {'jsinterp': 'Field access is not supported'}

tests = [
    {
        'code': 'function f() { return a.var; }',
        'asserts': [{'value': 3, 'call': ('f',)}],
        'globals': {'a': {'var': 3}},
        'ast': [
            (TokenTypes.FUNC, 'f', [], [
                (TokenTypes.RETURN,
                 (TokenTypes.EXPR, [
                     (TokenTypes.ASSIGN,
                      None,
                      (TokenTypes.OPEXPR, [
                          (TokenTypes.MEMBER,
                           (TokenTypes.ID, 'a'),
                           None,
                           (TokenTypes.FIELD, 'var', None)),
                      ]),
                      None)
                 ]))
            ])
        ]
    }
]
