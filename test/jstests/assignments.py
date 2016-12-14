from youtube_dl.jsinterp.jsgrammar import Token
from youtube_dl.jsinterp.tstream import _OPERATORS, _ASSIGN_OPERATORS

tests = [
    {
        'code': 'var x = 20; x = 30 + 1; return x;',
        'asserts': [{'value': 31}],
        'ast': [
            (Token.VAR, zip(
                ['x'],
                [(Token.ASSIGN,
                  None,
                  (Token.OPEXPR, [(Token.MEMBER, (Token.INT, 20), None, None)]),
                  None)]
            )),
            (Token.EXPR, [
                (Token.ASSIGN,
                 _ASSIGN_OPERATORS['='][1],
                 (Token.OPEXPR, [(Token.MEMBER, (Token.ID, 'x'), None, None)]),
                 (Token.ASSIGN, None,
                  (Token.OPEXPR, [
                      (Token.MEMBER, (Token.INT, 30), None, None),
                      (Token.MEMBER, (Token.INT, 1), None, None),
                      (Token.OP, _OPERATORS['+'][1])]),
                  None))
            ]),

            (Token.RETURN, (Token.EXPR, [
                (Token.ASSIGN, None,
                 (Token.OPEXPR, [
                     (Token.MEMBER, (Token.ID, 'x'), None, None)
                 ]), None)
            ]))
        ]
    }, {
        'code': 'var x = 20; x += 30 + 1; return x;',
        'asserts': [{'value': 51}],
    }, {
        'code': 'var x = 20; x -= 30 + 1; return x;',
        'asserts': [{'value': -11}],
    }
]
