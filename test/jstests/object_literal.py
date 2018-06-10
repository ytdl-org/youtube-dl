from __future__ import unicode_literals

from youtube_dl.jsinterp2.jsgrammar import TokenTypes
from youtube_dl.jsinterp2.tstream import _ASSIGN_OPERATORS, _OPERATORS

skip = {
    'jsinterp': 'Unsupported JS expression',
    'interpret': 'Interpreting object literals is not yet implemented'
}

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
            (TokenTypes.FUNC, 'f', [], [
                (TokenTypes.VAR,
                 zip(['o'],
                     [(TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                         (TokenTypes.MEMBER, (TokenTypes.OBJECT, [
                             ('a', (TokenTypes.PROPVALUE, (TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                                 (TokenTypes.MEMBER, (TokenTypes.INT, 7), None, None)
                             ]), None))),
                             ('b', (TokenTypes.PROPGET, [
                                 (TokenTypes.RETURN, (TokenTypes.EXPR, [(TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                                     (TokenTypes.MEMBER, (TokenTypes.RSV, 'this'), None, (TokenTypes.FIELD, 'a', None)),
                                     (TokenTypes.MEMBER, (TokenTypes.INT, 1), None, None),
                                     (TokenTypes.OP, _OPERATORS['+'][1])
                                 ]), None)]))
                             ])),
                             ('c', (TokenTypes.PROPSET, 'x', [
                                 (TokenTypes.EXPR, [
                                     (TokenTypes.ASSIGN,
                                      _ASSIGN_OPERATORS['='][1],
                                      (TokenTypes.OPEXPR, [
                                          (TokenTypes.MEMBER, (TokenTypes.RSV, 'this'), None, (TokenTypes.FIELD, 'a', None))
                                      ]),
                                      (TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                                          (TokenTypes.MEMBER, (TokenTypes.ID, 'x'), None, None),
                                          (TokenTypes.MEMBER, (TokenTypes.INT, 2), None, None),
                                          (TokenTypes.OP, _OPERATORS['/'][1])
                                      ]), None))
                                 ])
                             ]))
                         ]),
                          None, None)
                     ]), None)]
                     )
                 ),
                (TokenTypes.RETURN, (TokenTypes.EXPR, [(TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                    (TokenTypes.MEMBER, (TokenTypes.ID, 'o'), None, None)]), None)]))
            ])
        ]
    }
]
