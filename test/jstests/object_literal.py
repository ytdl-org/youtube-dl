from youtube_dl.jsinterp.jsgrammar import Token
from youtube_dl.jsinterp.tstream import _ASSIGN_OPERATORS, _OPERATORS

skip = {'i': 'Interpreting object literals not yet implemented'}

tests = [
    {
        'code': '''
            function f() {
                var o = {
                    a: 7,
                    get b() { return this.a + 1; },
                    set c(x) { this.a = x / 2; }
                };
                return o;
            }
            ''',
        'ast': [
            (Token.FUNC, 'f', [],
             (Token.BLOCK, [
                 (Token.VAR,
                  zip(['o'],
                      [(Token.ASSIGN, None, (Token.OPEXPR, [
                          (Token.MEMBER, (Token.OBJECT, [
                              ('a', (Token.PROPVALUE, (Token.ASSIGN, None, (Token.OPEXPR, [
                                  (Token.MEMBER, (Token.INT, 7), None, None)
                              ]), None))),
                              ('b', (Token.PROPGET, (Token.BLOCK, [
                                  (Token.RETURN, (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                                      (Token.MEMBER, (Token.RSV, 'this'), None, (Token.FIELD, 'a', None)),
                                      (Token.MEMBER, (Token.INT, 1), None, None),
                                      (Token.OP, _OPERATORS['+'][1])
                                  ]), None)]))
                              ]))),
                              ('c', (Token.PROPSET, 'x', (Token.BLOCK, [
                                  (Token.EXPR, [
                                      (Token.ASSIGN,
                                       _ASSIGN_OPERATORS['='][1],
                                       (Token.OPEXPR, [
                                           (Token.MEMBER, (Token.RSV, 'this'), None, (Token.FIELD, 'a', None))
                                       ]),
                                       (Token.ASSIGN, None, (Token.OPEXPR, [
                                           (Token.MEMBER, (Token.ID, 'x'), None, None),
                                           (Token.MEMBER, (Token.INT, 2), None, None),
                                           (Token.OP, _OPERATORS['/'][1])
                                       ]), None))
                                  ])
                              ])))
                          ]),
                           None, None)
                      ]), None)]
                      )
                  ),
                 (Token.RETURN, (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                     (Token.MEMBER, (Token.ID, 'o'), None, None)]), None)]))
             ]))
        ]
    }
]
