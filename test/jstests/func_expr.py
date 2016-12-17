from youtube_dl.jsinterp.jsgrammar import Token
from youtube_dl.jsinterp.tstream import _ASSIGN_OPERATORS

skip = {'i': 'Interpreting function expression not yet implemented'}

tests = [
    {
        'code': '''
            function f() {
                var add = (function () {
                    var counter = 0;
                    return function () {return counter += 1;};
                })();
                add();
                add();
                return add();
            }
            ''',
        'asserts': [{'value': 3, 'call': ('f',)}],
        'ast': [
            (Token.FUNC, 'f', [], [
                (Token.VAR, zip(['add'], [(Token.ASSIGN, None, (Token.OPEXPR, [
                    (Token.MEMBER, (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                        (Token.MEMBER, (Token.FUNC, None, [], [
                            (Token.VAR, zip(
                                ['counter'],
                                [(Token.ASSIGN, None, (Token.OPEXPR, [
                                    (Token.MEMBER, (Token.INT, 0), None, None)
                                ]), None)]
                            )),
                            (Token.RETURN, (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                                (Token.MEMBER, (Token.FUNC, None, [], [
                                    (Token.RETURN, (Token.EXPR, [
                                        (Token.ASSIGN, _ASSIGN_OPERATORS['+='][1], (Token.OPEXPR, [
                                            (Token.MEMBER, (Token.ID, 'counter'), None, None)
                                        ]), (Token.ASSIGN, None, (Token.OPEXPR, [
                                            (Token.MEMBER, (Token.INT, 1), None, None)
                                        ]), None))
                                    ]))
                                ]), None, None)
                            ]), None)]))
                        ]), None, None),
                    ]), None)]), None, (Token.CALL, [], None))
                ]), None)])),
                (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                    (Token.MEMBER, (Token.ID, 'add'), None, (Token.CALL, [], None))
                ]), None)]),
                (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                    (Token.MEMBER, (Token.ID, 'add'), None, (Token.CALL, [], None))
                ]), None)]),
                (Token.RETURN, (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                    (Token.MEMBER, (Token.ID, 'add'), None, (Token.CALL, [], None))
                ]), None)]))
            ])
        ]
    }
]
