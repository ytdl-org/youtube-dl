from __future__ import unicode_literals

from youtube_dl.jsinterp2.jsgrammar import TokenTypes
from youtube_dl.jsinterp2.tstream import _ASSIGN_OPERATORS, _OPERATORS

skip = {'interpret': 'Interpreting built-in fields are not yet implemented'}

tests = [
    {
        'code': '''
            function f() { 
                var a = [10, 20, 30, 40, 50];
                var b = 6;
                a[0]=a[b%a.length];
                return a;
            }
            ''',
        'asserts': [{'value': [20, 20, 30, 40, 50], 'call': ('f',)}],
        'ast': [
            (TokenTypes.FUNC, 'f', [], [
                (TokenTypes.VAR,
                 zip(['a'],
                     [(TokenTypes.ASSIGN,
                       None,
                       (TokenTypes.OPEXPR, [
                           (TokenTypes.MEMBER, (TokenTypes.ARRAY, [
                               (TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                                   (TokenTypes.MEMBER, (TokenTypes.INT, 10), None, None)]), None),
                               (TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                                   (TokenTypes.MEMBER, (TokenTypes.INT, 20), None, None)]), None),
                               (TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                                   (TokenTypes.MEMBER, (TokenTypes.INT, 30), None, None)]), None),
                               (TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                                   (TokenTypes.MEMBER, (TokenTypes.INT, 40), None, None)]), None),
                               (TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                                   (TokenTypes.MEMBER, (TokenTypes.INT, 50), None, None)]), None)
                           ]), None, None),
                       ]),
                       None)
                      ])
                 ),
                (TokenTypes.VAR,
                 zip(['b'],
                     [(TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [(TokenTypes.MEMBER, (TokenTypes.INT, 6), None, None)]), None)]
                     )
                 ),
                (TokenTypes.EXPR, [
                    (TokenTypes.ASSIGN,
                     _ASSIGN_OPERATORS['='][1],
                     (TokenTypes.OPEXPR, [
                         (TokenTypes.MEMBER, (TokenTypes.ID, 'a'),
                          None,
                          (TokenTypes.ELEM,
                           (TokenTypes.EXPR, [
                               (TokenTypes.ASSIGN,
                                None,
                                (TokenTypes.OPEXPR, [(TokenTypes.MEMBER, (TokenTypes.INT, 0), None, None)]),
                                None)
                           ]),
                           None))
                     ]),
                     (TokenTypes.ASSIGN,
                      None,
                      (TokenTypes.OPEXPR, [
                          (TokenTypes.MEMBER, (TokenTypes.ID, 'a'),
                           None,
                           (TokenTypes.ELEM, (TokenTypes.EXPR, [
                               (TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                                   (TokenTypes.MEMBER, (TokenTypes.ID, 'b'), None, None),
                                   (TokenTypes.MEMBER, (TokenTypes.ID, 'a'), None, (TokenTypes.FIELD, 'length', None)),
                                   (TokenTypes.OP, _OPERATORS['%'][1])
                               ]), None)]),
                            None))
                      ]),
                      None)
                     )
                ]),
                (TokenTypes.RETURN,
                 (TokenTypes.EXPR, [
                     (TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [(TokenTypes.MEMBER, (TokenTypes.ID, 'a'), None, None)]), None)
                 ])
                 )
            ])
        ]
    }
]
