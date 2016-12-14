from youtube_dl.jsinterp.jsgrammar import Token
from youtube_dl.jsinterp.tstream import _OPERATORS

tests = [
    {
        'code': '''
            var x = /* 1 + */ 2;
            var y = /* 30
            * 40 */ 50;
            return x + y;''',
        'asserts': [{'value': 52}],
        'ast': [
            (Token.VAR, zip(
                ['x'],
                [(Token.ASSIGN,
                  None,
                  (Token.OPEXPR, [(Token.MEMBER, (Token.INT, 2), None, None)]),
                  None)]
            )),
            (Token.VAR, zip(
                ['y'],
                [(Token.ASSIGN,
                  None,
                  (Token.OPEXPR, [(Token.MEMBER, (Token.INT, 50), None, None)]),
                  None)]
            )),
            (Token.RETURN, (Token.EXPR, [
                (Token.ASSIGN, None,
                 (Token.OPEXPR, [
                     (Token.MEMBER, (Token.ID, 'x'), None, None),
                     (Token.MEMBER, (Token.ID, 'y'), None, None),
                     (Token.OP, _OPERATORS['+'][1])
                 ]), None)
            ]))
        ]
    }, {
        'code': '''
            var x = "/*";
            var y = 1 /* comment */ + 2;
            return y;
        ''',
        'asserts': [{'value': 3}],
        'ast': [
            (Token.VAR, zip(
                ['x'],
                [(Token.ASSIGN,
                  None,
                  (Token.OPEXPR, [(Token.MEMBER, (Token.STR, '/*'), None, None)]),
                  None)]
            )),
            (Token.VAR, zip(
                ['y'],
                [(Token.ASSIGN,
                  None,
                  (Token.OPEXPR, [
                      (Token.MEMBER, (Token.INT, 1), None, None),
                      (Token.MEMBER, (Token.INT, 2), None, None),
                      (Token.OP, _OPERATORS['+'][1])
                  ]),
                  None)]
            )),
            (Token.RETURN, (Token.EXPR, [
                (Token.ASSIGN, None,
                 (Token.OPEXPR, [(Token.MEMBER, (Token.ID, 'y'), None, None)]),
                 None)
            ]))
        ]
    }
]
