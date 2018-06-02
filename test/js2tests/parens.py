from __future__ import unicode_literals

from youtube_dl.jsinterp2.jsgrammar import Token
from youtube_dl.jsinterp2.tstream import _OPERATORS

tests = [
    {
        'code': 'function f() { return (1 + 2) * 3; }',
        'asserts': [{'value': 9, 'call': ('f',)}],
        'ast': [
            (Token.FUNC, 'f', [], [
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
                ]))
            ])
        ]
    }, {
        'code': 'function f() { return (1) + (2) * ((( (( (((((3)))))) )) ));}',
        'asserts': [{'value': 7, 'call': ('f',)}],
        'ast': [
            (Token.FUNC, 'f', [], [
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
            ])
        ]
    }
]
