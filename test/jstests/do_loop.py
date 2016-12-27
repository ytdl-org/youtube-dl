from youtube_dl.jsinterp.jsgrammar import Token
from youtube_dl.jsinterp.tstream import _ASSIGN_OPERATORS, _UNARY_OPERATORS, _RELATIONS

skip = {'interpret': 'Interpreting do loop not yet implemented'}

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
        'asserts': [{'value': 5, 'call': 5}],
        'ast': [
            (Token.FUNC, 'f', ['x'], [
                (Token.EXPR, [
                    (Token.ASSIGN, _ASSIGN_OPERATORS['='][1],
                     (Token.OPEXPR, [(Token.MEMBER, (Token.ID, 'i'), None, None)]),
                     (Token.ASSIGN, None, (Token.OPEXPR, [(Token.MEMBER, (Token.INT, 1), None, None)]), None))
                ]),
                (Token.DO,
                 (Token.EXPR, [
                     (Token.ASSIGN, None, (Token.OPEXPR, [
                         (Token.MEMBER, (Token.ID, 'i'), None, None),
                         (Token.MEMBER, (Token.ID, 'x'), None, None),
                         (Token.REL, _RELATIONS['<'][1])
                     ]), None)
                 ]),
                 (Token.BLOCK, [
                     (Token.EXPR, [
                         (Token.ASSIGN, None, (Token.OPEXPR, [
                             (Token.MEMBER, (Token.ID, 'i'), None, None),
                             (Token.POSTFIX, _UNARY_OPERATORS['++'][1])
                         ]), None)
                     ])
                 ])),
                (Token.RETURN, (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                    (Token.MEMBER, (Token.ID, 'i'), None, None)]), None)]))
            ])
        ]
    }
]
