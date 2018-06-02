from __future__ import unicode_literals

from youtube_dl.jsinterp2.jsgrammar import Token
from youtube_dl.jsinterp2.tstream import _ASSIGN_OPERATORS

tests = [
    {'code': 'function f() { var x = [1,2,3]; x[0] = 4; x[0] = 5; x[2] = 7; return x; }',
     'asserts': [{'value': [5, 2, 7], 'call': ('f',)}],
         'ast': [
             (Token.FUNC, 'f', [], [
                 (Token.VAR,
                  zip(['x'],
                      [(Token.ASSIGN,
                        None,
                        (Token.OPEXPR, [
                            (Token.MEMBER, (Token.ARRAY, [
                                (Token.ASSIGN, None, (Token.OPEXPR, [
                                    (Token.MEMBER, (Token.INT, 1), None, None)]), None),
                                (Token.ASSIGN, None, (Token.OPEXPR, [
                                    (Token.MEMBER, (Token.INT, 2), None, None)]), None),
                                (Token.ASSIGN, None, (Token.OPEXPR, [
                                    (Token.MEMBER, (Token.INT, 3), None, None)]), None)
                            ]), None, None),
                        ]),
                        None)
                       ])
                  ),
                 (Token.EXPR, [
                     (Token.ASSIGN,
                      _ASSIGN_OPERATORS['='][1],
                      (Token.OPEXPR, [
                          (Token.MEMBER, (Token.ID, 'x'),
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
                      (Token.ASSIGN, None, (Token.OPEXPR, [(Token.MEMBER, (Token.INT, 4), None, None)]), None)
                      )
                 ]),
                 (Token.EXPR, [
                     (Token.ASSIGN,
                      _ASSIGN_OPERATORS['='][1],
                      (Token.OPEXPR, [(Token.MEMBER, (Token.ID, 'x'),
                                       None,
                                       (Token.ELEM, (Token.EXPR, [
                                           (Token.ASSIGN,
                                            None,
                                            (Token.OPEXPR, [(Token.MEMBER, (Token.INT, 0), None, None)]),
                                            None)
                                       ]), None))
                                      ]),
                      (Token.ASSIGN, None, (Token.OPEXPR, [(Token.MEMBER, (Token.INT, 5), None, None)]), None))
                 ]),
                 (Token.EXPR, [
                     (Token.ASSIGN,
                      _ASSIGN_OPERATORS['='][1],
                      (Token.OPEXPR, [(Token.MEMBER, (Token.ID, 'x'),
                                       None,
                                       (Token.ELEM, (Token.EXPR, [
                                           (Token.ASSIGN,
                                            None,
                                            (Token.OPEXPR, [(Token.MEMBER, (Token.INT, 2), None, None)]),
                                            None)
                                       ]), None))
                                      ]),
                      (Token.ASSIGN, None, (Token.OPEXPR, [(Token.MEMBER, (Token.INT, 7), None, None)]), None))
                 ]),
                 (Token.RETURN,
                  (Token.EXPR, [
                      (Token.ASSIGN, None, (Token.OPEXPR, [(Token.MEMBER, (Token.ID, 'x'), None, None)]), None)
                  ])
                  )
             ])
         ]
     }
]
