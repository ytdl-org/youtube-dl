from youtube_dl.jsinterp.jsgrammar import Token

tests = [
    {
        'code': 'return a.var;',
        'asserts': [{'value': 3}],
        'globals': {'a': {'var': 3}},
        'ast': [
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
        ]
    }
]
