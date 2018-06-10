from __future__ import unicode_literals

from youtube_dl.jsinterp2.jsgrammar import TokenTypes
from youtube_dl.jsinterp2.tstream import _ASSIGN_OPERATORS

skip = {
    'jsinterp': 'not supported',
    'interpret': 'Interpreting function expression is not yet implemented'
}

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
            (TokenTypes.FUNC, 'f', [], [
                (TokenTypes.VAR, zip(['add'], [(TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                    (TokenTypes.MEMBER, (TokenTypes.EXPR, [(TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                        (TokenTypes.MEMBER, (TokenTypes.FUNC, None, [], [
                            (TokenTypes.VAR, zip(
                                ['counter'],
                                [(TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                                    (TokenTypes.MEMBER, (TokenTypes.INT, 0), None, None)
                                ]), None)]
                            )),
                            (TokenTypes.RETURN, (TokenTypes.EXPR, [(TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                                (TokenTypes.MEMBER, (TokenTypes.FUNC, None, [], [
                                    (TokenTypes.RETURN, (TokenTypes.EXPR, [
                                        (TokenTypes.ASSIGN, _ASSIGN_OPERATORS['+='][1], (TokenTypes.OPEXPR, [
                                            (TokenTypes.MEMBER, (TokenTypes.ID, 'counter'), None, None)
                                        ]), (TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                                            (TokenTypes.MEMBER, (TokenTypes.INT, 1), None, None)
                                        ]), None))
                                    ]))
                                ]), None, None)
                            ]), None)]))
                        ]), None, None),
                    ]), None)]), None, (TokenTypes.CALL, [], None))
                ]), None)])),
                (TokenTypes.EXPR, [(TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                    (TokenTypes.MEMBER, (TokenTypes.ID, 'add'), None, (TokenTypes.CALL, [], None))
                ]), None)]),
                (TokenTypes.EXPR, [(TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                    (TokenTypes.MEMBER, (TokenTypes.ID, 'add'), None, (TokenTypes.CALL, [], None))
                ]), None)]),
                (TokenTypes.RETURN, (TokenTypes.EXPR, [(TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                    (TokenTypes.MEMBER, (TokenTypes.ID, 'add'), None, (TokenTypes.CALL, [], None))
                ]), None)]))
            ])
        ]
    }
]
