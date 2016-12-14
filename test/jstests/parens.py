from youtube_dl.jsinterp.jsgrammar import Token
from youtube_dl.jsinterp.tstream import _OPERATORS

tests = [
    {
        'code': 'return (1 + 2) * 3;',
        'asserts': [{'value': 9}],
        'ast': [
            (Token.RETURN, (Token.EXPR, [
                (Token.ASSIGN, None,
                 (Token.OPEXPR, [
                     (Token.MEMBER, (Token.EXPR, [
                         (Token.ASSIGN, None,
                          (Token.OPEXPR, [
                              (Token.MEMBER, (Token.INT, 1), None, None),
                              (Token.MEMBER, (Token.INT, 2), None, None),
                              (Token.OP, _OPERATORS['+'][1])
                          ]), None)
                     ]), None, None),
                     (Token.MEMBER, (Token.INT, 3), None, None),
                     (Token.OP, _OPERATORS['*'][1])
                 ]), None)
            ]))]
    }, {
        'code': 'return (1) + (2) * ((( (( (((((3)))))) )) ));',
        'asserts': [{'value': 7}],
        'ast': [

            (Token.RETURN, (Token.EXPR, [
                (Token.ASSIGN, None,
                 (Token.OPEXPR, [
                     (Token.MEMBER, (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                         (Token.MEMBER, (Token.INT, 1), None, None)
                     ]), None)]), None, None),

                     (Token.MEMBER, (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                         (Token.MEMBER, (Token.INT, 2), None, None)
                     ]), None)]), None, None),

                     (Token.MEMBER, (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                         (Token.MEMBER, (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                             (Token.MEMBER, (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [

                                 (Token.MEMBER, (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                                     (Token.MEMBER, (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [

                                         (Token.MEMBER, (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                                             (Token.MEMBER, (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                                                 (Token.MEMBER, (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                                                     (Token.MEMBER, (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                                                         (Token.MEMBER,
                                                          (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                                                              (Token.MEMBER, (Token.INT, 3), None, None)
                                                          ]), None)]), None, None)
                                                     ]), None)]), None, None)
                                                 ]), None)]), None, None)
                                             ]), None)]), None, None)
                                         ]), None)]), None, None)

                                     ]), None)]), None, None)
                                 ]), None)]), None, None)

                             ]), None)]), None, None)
                         ]), None)]), None, None)
                     ]), None)]), None, None),

                     (Token.OP, _OPERATORS['*'][1]),
                     (Token.OP, _OPERATORS['+'][1])
                 ]), None)
            ]))
        ]
    }
]
