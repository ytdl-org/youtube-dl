from __future__ import unicode_literals

from youtube_dl.jsinterp2.jsgrammar import TokenTypes
from youtube_dl.jsinterp2.tstream import _ASSIGN_OPERATORS

tests = [
    {'code': 'function f() { var x = [1,2,3]; x[0] = 4; x[0] = 5; x[2] = 7; return x; }',
     'asserts': [{'value': [5, 2, 7], 'call': ('f',)}],
     'ast': [
         (TokenTypes.FUNC, 'f', [], [
             (TokenTypes.VAR,
              zip(['x'],
                  [(TokenTypes.ASSIGN,
                    None,
                    (TokenTypes.OPEXPR, [
                        (TokenTypes.MEMBER, (TokenTypes.ARRAY, [
                            (TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                                (TokenTypes.MEMBER, (TokenTypes.INT, 1), None, None)]), None),
                            (TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                                (TokenTypes.MEMBER, (TokenTypes.INT, 2), None, None)]), None),
                            (TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                                (TokenTypes.MEMBER, (TokenTypes.INT, 3), None, None)]), None)
                        ]), None, None),
                    ]),
                    None)
                   ])
              ),
             (TokenTypes.EXPR, [
                 (TokenTypes.ASSIGN,
                  _ASSIGN_OPERATORS['='][1],
                  (TokenTypes.OPEXPR, [
                      (TokenTypes.MEMBER, (TokenTypes.ID, 'x'),
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
                  (TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [(TokenTypes.MEMBER, (TokenTypes.INT, 4), None, None)]), None)
                  )
             ]),
             (TokenTypes.EXPR, [
                 (TokenTypes.ASSIGN,
                  _ASSIGN_OPERATORS['='][1],
                  (TokenTypes.OPEXPR, [(TokenTypes.MEMBER, (TokenTypes.ID, 'x'),
                                        None,
                                        (TokenTypes.ELEM, (TokenTypes.EXPR, [
                                       (TokenTypes.ASSIGN,
                                        None,
                                        (TokenTypes.OPEXPR, [(TokenTypes.MEMBER, (TokenTypes.INT, 0), None, None)]),
                                        None)
                                   ]), None))
                                       ]),
                  (TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [(TokenTypes.MEMBER, (TokenTypes.INT, 5), None, None)]), None))
             ]),
             (TokenTypes.EXPR, [
                 (TokenTypes.ASSIGN,
                  _ASSIGN_OPERATORS['='][1],
                  (TokenTypes.OPEXPR, [(TokenTypes.MEMBER, (TokenTypes.ID, 'x'),
                                        None,
                                        (TokenTypes.ELEM, (TokenTypes.EXPR, [
                                       (TokenTypes.ASSIGN,
                                        None,
                                        (TokenTypes.OPEXPR, [(TokenTypes.MEMBER, (TokenTypes.INT, 2), None, None)]),
                                        None)
                                   ]), None))
                                       ]),
                  (TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [(TokenTypes.MEMBER, (TokenTypes.INT, 7), None, None)]), None))
             ]),
             (TokenTypes.RETURN,
              (TokenTypes.EXPR, [
                  (TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [(TokenTypes.MEMBER, (TokenTypes.ID, 'x'), None, None)]), None)
              ])
              )
         ])
     ]
     }
]
