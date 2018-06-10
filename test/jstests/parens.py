from __future__ import unicode_literals

from youtube_dl.jsinterp2.jsgrammar import TokenTypes
from youtube_dl.jsinterp2.tstream import _OPERATORS

tests = [
    {
        'code': 'function f() { return (1 + 2) * 3; }',
        'asserts': [{'value': 9, 'call': ('f',)}],
        'ast': [
            (TokenTypes.FUNC, 'f', [], [
                (TokenTypes.RETURN, (TokenTypes.EXPR, [
                    (TokenTypes.ASSIGN, None,
                     (TokenTypes.OPEXPR, [
                         (TokenTypes.MEMBER, (TokenTypes.EXPR, [
                             (TokenTypes.ASSIGN, None,
                              (TokenTypes.OPEXPR, [
                                  (TokenTypes.MEMBER, (TokenTypes.INT, 1), None, None),
                                  (TokenTypes.MEMBER, (TokenTypes.INT, 2), None, None),
                                  (TokenTypes.OP, _OPERATORS['+'][1])
                              ]), None)
                         ]), None, None),
                         (TokenTypes.MEMBER, (TokenTypes.INT, 3), None, None),
                         (TokenTypes.OP, _OPERATORS['*'][1])
                     ]), None)
                ]))
            ])
        ]
    }, {
        'code': 'function f() { return (1) + (2) * ((( (( (((((3)))))) )) ));}',
        'asserts': [{'value': 7, 'call': ('f',)}],
        'ast': [
            (TokenTypes.FUNC, 'f', [], [
                (TokenTypes.RETURN, (TokenTypes.EXPR, [
                    (TokenTypes.ASSIGN, None,
                     (TokenTypes.OPEXPR, [
                         (TokenTypes.MEMBER, (TokenTypes.EXPR, [(TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                             (TokenTypes.MEMBER, (TokenTypes.INT, 1), None, None)
                         ]), None)]), None, None),

                         (TokenTypes.MEMBER, (TokenTypes.EXPR, [(TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                             (TokenTypes.MEMBER, (TokenTypes.INT, 2), None, None)
                         ]), None)]), None, None),

                         (TokenTypes.MEMBER, (TokenTypes.EXPR, [(TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                             (TokenTypes.MEMBER, (TokenTypes.EXPR, [(TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                                 (TokenTypes.MEMBER, (TokenTypes.EXPR, [(TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [

                                     (TokenTypes.MEMBER, (TokenTypes.EXPR, [(TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                                         (TokenTypes.MEMBER, (TokenTypes.EXPR, [(TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [

                                             (TokenTypes.MEMBER, (TokenTypes.EXPR, [(TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                                                 (TokenTypes.MEMBER, (TokenTypes.EXPR, [(TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                                                     (TokenTypes.MEMBER, (TokenTypes.EXPR, [(TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                                                         (TokenTypes.MEMBER,
                                                          (TokenTypes.EXPR, [(TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                                                              (TokenTypes.MEMBER,
                                                               (TokenTypes.EXPR, [(TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                                                                   (TokenTypes.MEMBER, (TokenTypes.INT, 3), None, None)
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

                         (TokenTypes.OP, _OPERATORS['*'][1]),
                         (TokenTypes.OP, _OPERATORS['+'][1])
                     ]), None)
                ]))
            ])
        ]
    }
]
