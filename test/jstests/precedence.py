from youtube_dl.jsinterp.jsgrammar import Token
from youtube_dl.jsinterp.tstream import _ASSIGN_OPERATORS, _OPERATORS

skip = {'i': 'Interpreting get field not yet implemented'}

tests = [
    {
        'code': '''
            var a = [10, 20, 30, 40, 50];
            var b = 6;
            a[0]=a[b%a.length];
            return a;
            ''',
        'asserts': [{'value': [20, 20, 30, 40, 50]}],
        'ast': [
            (Token.VAR,
             zip(['a'],
                 [(Token.ASSIGN,
                   None,
                   (Token.OPEXPR, [
                       (Token.MEMBER, (Token.ARRAY, [
                           (Token.ASSIGN, None, (Token.OPEXPR, [
                               (Token.MEMBER, (Token.INT, 10), None, None)]), None),
                           (Token.ASSIGN, None, (Token.OPEXPR, [
                               (Token.MEMBER, (Token.INT, 20), None, None)]), None),
                           (Token.ASSIGN, None, (Token.OPEXPR, [
                               (Token.MEMBER, (Token.INT, 30), None, None)]), None),
                           (Token.ASSIGN, None, (Token.OPEXPR, [
                               (Token.MEMBER, (Token.INT, 40), None, None)]), None),
                           (Token.ASSIGN, None, (Token.OPEXPR, [
                               (Token.MEMBER, (Token.INT, 50), None, None)]), None)
                       ]), None, None),
                   ]),
                   None)
                  ])
             ),
            (Token.VAR,
             zip(['b'],
                 [(Token.ASSIGN, None, (Token.OPEXPR, [(Token.MEMBER, (Token.INT, 6), None, None)]), None)]
                 )
             ),
            (Token.EXPR, [
                (Token.ASSIGN,
                 _ASSIGN_OPERATORS['='][1],
                 (Token.OPEXPR, [
                     (Token.MEMBER, (Token.ID, 'a'),
                      None,
                      (Token.ELEM,
                       (Token.EXPR, [
                           (Token.ASSIGN,
                            None,
                            (Token.OPEXPR, [(Token.MEMBER, (Token.INT, 0), None, None)]),
                            None)
                       ]),
                       None))
                 ]),
                 (Token.ASSIGN,
                  None,
                  (Token.OPEXPR, [
                      (Token.MEMBER, (Token.ID, 'a'),
                       None,
                       (Token.ELEM, (Token.EXPR, [
                           (Token.ASSIGN, None, (Token.OPEXPR, [
                               (Token.MEMBER, (Token.ID, 'b'), None, None),
                               (Token.MEMBER, (Token.ID, 'a'), None, (Token.FIELD, 'length', None)),
                               (Token.OP, _OPERATORS['%'][1])
                           ]), None)]),
                        None))
                  ]),
                  None)
                 )
            ]),
            (Token.RETURN,
             (Token.EXPR, [
                 (Token.ASSIGN, None, (Token.OPEXPR, [(Token.MEMBER, (Token.ID, 'a'), None, None)]), None)
             ])
             )
        ]
    }
]
