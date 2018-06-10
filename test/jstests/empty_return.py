from __future__ import unicode_literals

from youtube_dl.jsinterp2.jsgrammar import Token

tests = [
    {'code': 'function f() { return; y(); }',
     'asserts': [{'value': None, 'call': ('f',)}],
     'ast': [
         (Token.FUNC, 'f', [], [
             (Token.RETURN, None),
             (Token.EXPR, [
                 (Token.ASSIGN,
                  None,
                  (Token.OPEXPR, [
                      (Token.MEMBER,
                       (Token.ID, 'y'),
                       None,
                       (Token.CALL, [], None)
                       )
                  ]),
                  None)
             ])
         ])
     ]
     }
]
