from __future__ import unicode_literals

from youtube_dl.jsinterp2.jsgrammar import TokenTypes
from youtube_dl.jsinterp2.tstream import _ASSIGN_OPERATORS, _UNARY_OPERATORS, _RELATIONS

skip = {
    'jsinterp': 'Do loop is not supported',
    'interpret': 'Interpreting do loop is not yet implemented'
}

tests = [
    {
        'code': '''
            function f(x){
                i = 1;
                do{
                    i++;
                } while (i < x);
                return i;
            }
            ''',
        'asserts': [{'value': 5, 'call': ('f', 5)}],
        'ast': [
            (TokenTypes.FUNC, 'f', ['x'], [
                (TokenTypes.EXPR, [
                    (TokenTypes.ASSIGN, _ASSIGN_OPERATORS['='][1],
                     (TokenTypes.OPEXPR, [(TokenTypes.MEMBER, (TokenTypes.ID, 'i'), None, None)]),
                     (TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [(TokenTypes.MEMBER, (TokenTypes.INT, 1), None, None)]), None))
                ]),
                (TokenTypes.DO,
                 (TokenTypes.EXPR, [
                     (TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                         (TokenTypes.MEMBER, (TokenTypes.ID, 'i'), None, None),
                         (TokenTypes.MEMBER, (TokenTypes.ID, 'x'), None, None),
                         (TokenTypes.REL, _RELATIONS['<'][1])
                     ]), None)
                 ]),
                 (TokenTypes.BLOCK, [
                     (TokenTypes.EXPR, [
                         (TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                             (TokenTypes.MEMBER, (TokenTypes.ID, 'i'), None, None),
                             (TokenTypes.POSTFIX, _UNARY_OPERATORS['++'][1])
                         ]), None)
                     ])
                 ])),
                (TokenTypes.RETURN, (TokenTypes.EXPR, [(TokenTypes.ASSIGN, None, (TokenTypes.OPEXPR, [
                    (TokenTypes.MEMBER, (TokenTypes.ID, 'i'), None, None)]), None)]))
            ])
        ]
    }
]
