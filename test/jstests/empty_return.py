from youtube_dl.jsinterp.jsgrammar import Token

tests = [
    {'code': 'return; y()',
     'asserts': [{'value': None}],
     'ast': [
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
         ])]
     }
]
