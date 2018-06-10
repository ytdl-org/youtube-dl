from __future__ import unicode_literals

from youtube_dl.jsinterp2.jsgrammar import TokenTypes

tests = [
    {'code': 'function f() { return; y(); }',
     'asserts': [{'value': None, 'call': ('f',)}],
     'ast': [
         (TokenTypes.FUNC, 'f', [], [
             (TokenTypes.RETURN, None),
             (TokenTypes.EXPR, [
                 (TokenTypes.ASSIGN,
                  None,
                  (TokenTypes.OPEXPR, [
                      (TokenTypes.MEMBER,
                       (TokenTypes.ID, 'y'),
                       None,
                       (TokenTypes.CALL, [], None)
                       )
                  ]),
                  None)
             ])
         ])
     ]
     }
]
