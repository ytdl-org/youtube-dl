#!/usr/bin/env python

from __future__ import unicode_literals

# Allow direct execution
import os
import sys
import copy

if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from youtube_dl.jsinterp import JSInterpreter
from youtube_dl.jsinterp.jsgrammar import Token
from youtube_dl.jsinterp.tstream import (
    _OPERATORS,
    _ASSIGN_OPERATORS,
    _LOGICAL_OPERATORS,
    _UNARY_OPERATORS,
    _RELATIONS
)


def traverse(node, tree_types=(list, tuple)):
    if type(node) == zip:
        node = list(copy.deepcopy(node))
    if isinstance(node, tree_types):
        for value in node:
            for subvalue in traverse(value, tree_types):
                yield subvalue
    else:
        yield node


class TestJSInterpreterParser(unittest.TestCase):
    def test_basic(self):
        jsi = JSInterpreter(';')
        ast = [None]
        self.assertEqual(list(jsi.statements()), ast)

        jsi = JSInterpreter('return 42;')
        ast = [(Token.RETURN,
                (Token.EXPR, [
                    (Token.ASSIGN,
                     None,
                     (Token.OPEXPR, [(Token.MEMBER, (Token.INT, 42), None, None)]),
                     None)
                ])
                )]
        self.assertEqual(list(jsi.statements()), ast)

    def test_calc(self):
        jsi = JSInterpreter('return 2*a+1;')
        ast = [(Token.RETURN,
                (Token.EXPR, [
                    (Token.ASSIGN,
                     None,
                     (Token.OPEXPR, [
                         # Reverse Polish Notation!
                         (Token.MEMBER, (Token.INT, 2), None, None),
                         (Token.MEMBER, (Token.ID, 'a'), None, None),
                         (Token.OP, _OPERATORS['*'][1]),
                         (Token.MEMBER, (Token.INT, 1), None, None),
                         (Token.OP, _OPERATORS['+'][1])
                     ]),
                     None)
                ])
                )]
        self.assertEqual(list(jsi.statements()), ast)

    def test_empty_return(self):
        jsi = JSInterpreter('return; y()')
        ast = [(Token.RETURN, None),
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
        self.assertEqual(list(jsi.statements()), ast)

    def test_morespace(self):
        jsi = JSInterpreter('x =  2  ; return x;')
        ast = [(Token.EXPR,
                [(Token.ASSIGN,
                  _ASSIGN_OPERATORS['='][1],
                  (Token.OPEXPR, [(Token.MEMBER, (Token.ID, 'x'), None, None)]),
                  (Token.ASSIGN,
                   None,
                   (Token.OPEXPR, [(Token.MEMBER, (Token.INT, 2), None, None)]),
                   None)
                  )]
                ),
               (Token.RETURN,
                (Token.EXPR, [
                    (Token.ASSIGN,
                     None,
                     (Token.OPEXPR, [(Token.MEMBER, (Token.ID, 'x'), None, None)]),
                     None)
                ])
                )]
        self.assertEqual(list(jsi.statements()), ast)

    def test_strange_chars(self):
        jsi = JSInterpreter('var $_axY2 = $_axY1 + 1; return $_axY2;')
        ast = [(Token.VAR,
                zip(['$_axY2'],
                    [(Token.ASSIGN,
                      None,
                      (Token.OPEXPR, [
                          (Token.MEMBER, (Token.ID, '$_axY1'), None, None),
                          (Token.MEMBER, (Token.INT, 1), None, None),
                          (Token.OP, _OPERATORS['+'][1])
                      ]),
                      None)
                     ])
                ),
               (Token.RETURN,
                (Token.EXPR, [
                    (Token.ASSIGN,
                     None,
                     (Token.OPEXPR, [(Token.MEMBER, (Token.ID, '$_axY2'), None, None)]),
                     None)]
                 )
                )]
        self.assertEqual(list(traverse(list(jsi.statements()))), list(traverse(ast)))

    def test_operators(self):
        jsi = JSInterpreter('return 1 << 5;')
        ast = [
            (Token.RETURN,
             (Token.EXPR, [
                 (Token.ASSIGN, None, (Token.OPEXPR, [
                     (Token.MEMBER, (Token.INT, 1), None, None),
                     (Token.MEMBER, (Token.INT, 5), None, None),
                     (Token.OP, _OPERATORS['<<'][1])
                 ]), None)
             ]))
        ]
        self.assertEqual(list(jsi.statements()), ast)

        jsi = JSInterpreter('return 19 & 21;')
        ast = [
            (Token.RETURN,
             (Token.EXPR, [
                 (Token.ASSIGN, None, (Token.OPEXPR, [
                     (Token.MEMBER, (Token.INT, 19), None, None),
                     (Token.MEMBER, (Token.INT, 21), None, None),
                     (Token.OP, _OPERATORS['&'][1])
                 ]), None)
             ]))
        ]
        self.assertEqual(list(jsi.statements()), ast)

        jsi = JSInterpreter('return 11 >> 2;')
        ast = [
            (Token.RETURN,
             (Token.EXPR, [
                 (Token.ASSIGN, None, (Token.OPEXPR, [
                     (Token.MEMBER, (Token.INT, 11), None, None),
                     (Token.MEMBER, (Token.INT, 2), None, None),
                     (Token.OP, _OPERATORS['>>'][1])
                 ]), None)
             ]))
        ]
        self.assertEqual(list(jsi.statements()), ast)

    def test_array_access(self):
        jsi = JSInterpreter('var x = [1,2,3]; x[0] = 4; x[0] = 5; x[2] = 7; return x;')
        ast = [(Token.VAR,
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
               ]
        self.assertEqual(list(traverse(list(jsi.statements()))), list(traverse(ast)))

    def test_parens(self):
        jsi = JSInterpreter('return (1 + 2) * 3;')
        ast = [
            (Token.RETURN, (Token.EXPR, [
                (Token.ASSIGN, None,
                 (Token.OPEXPR, [
                     (Token.MEMBER, (Token.EXPR, [
                         (Token.ASSIGN, None,
                          (Token.OPEXPR, [
                              (Token.MEMBER, (Token.INT, 1), None, None),
                              (Token.MEMBER, (Token.INT, 2), None, None),
                              (Token.OP, _OPERATORS['+'][1])
                          ]), None)
                     ]), None, None),
                     (Token.MEMBER, (Token.INT, 3), None, None),
                     (Token.OP, _OPERATORS['*'][1])
                 ]), None)
            ]))
        ]
        self.assertEqual(list(jsi.statements()), ast)

        jsi = JSInterpreter('return (1) + (2) * ((( (( (((((3)))))) )) ));')
        ast = [
            (Token.RETURN, (Token.EXPR, [
                (Token.ASSIGN, None,
                 (Token.OPEXPR, [
                     (Token.MEMBER, (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                         (Token.MEMBER, (Token.INT, 1), None, None)
                     ]), None)]), None, None),

                     (Token.MEMBER, (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                         (Token.MEMBER, (Token.INT, 2), None, None)
                     ]), None)]), None, None),

                     (Token.MEMBER, (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                         (Token.MEMBER, (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                             (Token.MEMBER, (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [

                                 (Token.MEMBER, (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                                     (Token.MEMBER, (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [

                                         (Token.MEMBER, (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                                             (Token.MEMBER, (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                                                 (Token.MEMBER, (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                                                     (Token.MEMBER, (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                                                         (Token.MEMBER,
                                                          (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                                                              (Token.MEMBER, (Token.INT, 3), None, None)
                                                          ]), None)]), None, None)
                                                     ]), None)]), None, None)
                                                 ]), None)]), None, None)
                                             ]), None)]), None, None)
                                         ]), None)]), None, None)

                                     ]), None)]), None, None)
                                 ]), None)]), None, None)

                             ]), None)]), None, None)
                         ]), None)]), None, None)
                     ]), None)]), None, None),

                     (Token.OP, _OPERATORS['*'][1]),
                     (Token.OP, _OPERATORS['+'][1])
                 ]), None)
            ]))
        ]
        self.assertEqual(list(jsi.statements()), ast)

    def test_assignments(self):
        jsi = JSInterpreter('var x = 20; x = 30 + 1; return x;')
        ast = [
            (Token.VAR, zip(
                ['x'],
                [(Token.ASSIGN,
                  None,
                  (Token.OPEXPR, [(Token.MEMBER, (Token.INT, 20), None, None)]),
                  None)]
            )),

            (Token.EXPR, [
                (Token.ASSIGN,
                 _ASSIGN_OPERATORS['='][1],
                 (Token.OPEXPR, [(Token.MEMBER, (Token.ID, 'x'), None, None)]),
                 (Token.ASSIGN, None,
                  (Token.OPEXPR, [
                      (Token.MEMBER, (Token.INT, 30), None, None),
                      (Token.MEMBER, (Token.INT, 1), None, None),
                      (Token.OP, _OPERATORS['+'][1])]),
                  None))
            ]),

            (Token.RETURN, (Token.EXPR, [
                (Token.ASSIGN, None,
                 (Token.OPEXPR, [
                     (Token.MEMBER, (Token.ID, 'x'), None, None)
                 ]), None)
            ]))
        ]
        self.assertEqual(list(traverse(list(jsi.statements()))), list(traverse(ast)))

        jsi = JSInterpreter('var x = 20; x += 30 + 1; return x;')
        ast[1] = (Token.EXPR, [
            (Token.ASSIGN,
             _ASSIGN_OPERATORS['+='][1],
             (Token.OPEXPR, [(Token.MEMBER, (Token.ID, 'x'), None, None)]),
             (Token.ASSIGN, None,
              (Token.OPEXPR, [
                  (Token.MEMBER, (Token.INT, 30), None, None),
                  (Token.MEMBER, (Token.INT, 1), None, None),
                  (Token.OP, _OPERATORS['+'][1])]),
              None))
        ])
        self.assertEqual(list(traverse(list(jsi.statements()))), list(traverse(ast)))

        jsi = JSInterpreter('var x = 20; x -= 30 + 1; return x;')
        ast[1] = (Token.EXPR, [
            (Token.ASSIGN,
             _ASSIGN_OPERATORS['-='][1],
             (Token.OPEXPR, [(Token.MEMBER, (Token.ID, 'x'), None, None)]),
             (Token.ASSIGN, None,
              (Token.OPEXPR, [
                  (Token.MEMBER, (Token.INT, 30), None, None),
                  (Token.MEMBER, (Token.INT, 1), None, None),
                  (Token.OP, _OPERATORS['+'][1])]),
              None))
        ])
        self.assertEqual(list(traverse(list(jsi.statements()))), list(traverse(ast)))

    def test_comments(self):
        # var x =  2; var y = 50; return x + y;
        jsi = JSInterpreter('var x = /* 1 + */ 2; var y = /* 30 * 40 */ 50; return x + y;')
        ast = [
            (Token.VAR, zip(
                ['x'],
                [(Token.ASSIGN,
                  None,
                  (Token.OPEXPR, [(Token.MEMBER, (Token.INT, 2), None, None)]),
                  None)]
            )),

            (Token.VAR, zip(
                ['y'],
                [(Token.ASSIGN,
                  None,
                  (Token.OPEXPR, [(Token.MEMBER, (Token.INT, 50), None, None)]),
                  None)]
            )),

            (Token.RETURN, (Token.EXPR, [
                (Token.ASSIGN, None,
                 (Token.OPEXPR, [
                     (Token.MEMBER, (Token.ID, 'x'), None, None),
                     (Token.MEMBER, (Token.ID, 'y'), None, None),
                     (Token.OP, _OPERATORS['+'][1])
                 ]), None)
            ]))
        ]
        self.assertEqual(list(traverse(list(jsi.statements()))), list(traverse(ast)))

        # var x = "/*"; var y = 1 + 2; return y;
        jsi = JSInterpreter('var x = "/*"; var y = 1 /* comment */ + 2; return y;')
        ast = [
            (Token.VAR, zip(
                ['x'],
                [(Token.ASSIGN,
                  None,
                  (Token.OPEXPR, [(Token.MEMBER, (Token.STR, '/*'), None, None)]),
                  None)]
            )),

            (Token.VAR, zip(
                ['y'],
                [(Token.ASSIGN,
                  None,
                  (Token.OPEXPR, [
                      (Token.MEMBER, (Token.INT, 1), None, None),
                      (Token.MEMBER, (Token.INT, 2), None, None),
                      (Token.OP, _OPERATORS['+'][1])
                  ]),
                  None)]
            )),

            (Token.RETURN, (Token.EXPR, [
                (Token.ASSIGN, None,
                 (Token.OPEXPR, [(Token.MEMBER, (Token.ID, 'y'), None, None)]),
                 None)
            ]))
        ]
        self.assertEqual(list(traverse(list(jsi.statements()))), list(traverse(ast)))

    def test_precedence(self):
        jsi = JSInterpreter(' var a = [10, 20, 30, 40, 50]; var b = 6; a[0]=a[b%a.length]; return a;')
        ast = [
            (Token.VAR,
             zip(['a'],
                 [(Token.ASSIGN,
                   None,
                   (Token.OPEXPR, [
                       (Token.MEMBER, (Token.ARRAY, [
                           (Token.ASSIGN, None, (Token.OPEXPR, [
                               (Token.MEMBER, (Token.INT, 10), None, None)]), None),
                           (Token.ASSIGN, None, (Token.OPEXPR, [
                               (Token.MEMBER, (Token.INT, 20), None, None)]), None),
                           (Token.ASSIGN, None, (Token.OPEXPR, [
                               (Token.MEMBER, (Token.INT, 30), None, None)]), None),
                           (Token.ASSIGN, None, (Token.OPEXPR, [
                               (Token.MEMBER, (Token.INT, 40), None, None)]), None),
                           (Token.ASSIGN, None, (Token.OPEXPR, [
                               (Token.MEMBER, (Token.INT, 50), None, None)]), None)
                       ]), None, None),
                   ]),
                   None)
                  ])
             ),
            (Token.VAR,
             zip(['b'],
                 [(Token.ASSIGN, None, (Token.OPEXPR, [(Token.MEMBER, (Token.INT, 6), None, None)]), None)]
                 )
             ),
            (Token.EXPR, [
                (Token.ASSIGN,
                 _ASSIGN_OPERATORS['='][1],
                 (Token.OPEXPR, [
                     (Token.MEMBER, (Token.ID, 'a'),
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
                 (Token.ASSIGN,
                  None,
                  (Token.OPEXPR, [
                      (Token.MEMBER, (Token.ID, 'a'),
                       None,
                       (Token.ELEM, (Token.EXPR, [
                           (Token.ASSIGN, None, (Token.OPEXPR, [
                               (Token.MEMBER, (Token.ID, 'b'), None, None),
                               (Token.MEMBER, (Token.ID, 'a'), None, (Token.FIELD, 'length', None)),
                               (Token.OP, _OPERATORS['%'][1])
                           ]), None)]),
                        None))
                  ]),
                  None)
                 )
            ]),
            (Token.RETURN,
             (Token.EXPR, [
                 (Token.ASSIGN, None, (Token.OPEXPR, [(Token.MEMBER, (Token.ID, 'a'), None, None)]), None)
             ])
             )
        ]
        self.assertEqual(list(traverse(list(jsi.statements()))), list(traverse(ast)))

    def test_call(self):
        jsi = JSInterpreter('''
        function x() { return 2; }
        function y(a) { return x() + a; }
        function z() { return y(3); }
        ''')

        ast = [
            (Token.FUNC, 'x',
             [],
             (Token.BLOCK, [
                 (Token.RETURN, (Token.EXPR, [
                     (Token.ASSIGN, None, (Token.OPEXPR, [(Token.MEMBER, (Token.INT, 2), None, None)]), None)
                 ])
                  )
             ])),
            (Token.FUNC, 'y',
             ['a'],
             (Token.BLOCK, [
                 (Token.RETURN, (Token.EXPR, [
                     (Token.ASSIGN, None,
                      (Token.OPEXPR, [
                          (Token.MEMBER, (Token.ID, 'x'), None, (Token.CALL, [], None)),
                          (Token.MEMBER, (Token.ID, 'a'), None, None),
                          (Token.OP, _OPERATORS['+'][1])
                      ]), None)
                 ])
                  )
             ])),
            (Token.FUNC, 'z',
             [],
             (Token.BLOCK, [
                 (Token.RETURN, (Token.EXPR, [
                     (Token.ASSIGN, None, (Token.OPEXPR, [
                         (Token.MEMBER, (Token.ID, 'y'), None, (Token.CALL, [
                             (Token.ASSIGN, None, (Token.OPEXPR, [(Token.MEMBER, (Token.INT, 3), None, None)]), None)
                         ], None))
                     ]), None)
                 ])
                  )
             ]))
        ]
        self.assertEqual(list(jsi.statements()), ast)
        jsi = JSInterpreter('function x(a) { return a.split(""); }', variables={'a': 'abc'})
        ast = [
            (Token.FUNC, 'x',
             ['a'],
             (Token.BLOCK, [
                 (Token.RETURN, (Token.EXPR, [
                     (Token.ASSIGN, None, (Token.OPEXPR, [
                         (Token.MEMBER, (Token.ID, 'a'), None,
                          (Token.FIELD, 'split',
                           (Token.CALL, [
                               (Token.ASSIGN, None, (Token.OPEXPR, [(Token.MEMBER, (Token.STR, ''), None, None)]), None)
                           ], None))
                          )]),
                      None)
                 ])
                  )
             ]))
        ]
        self.assertEqual(list(jsi.statements()), ast)

    def test_complex_call(self):
        jsi = JSInterpreter('''
                function a(x) { return x; }
                function b(x) { return x; }
                function c()  { return [a, b][0](0); }
                ''')
        ast = [
            (Token.FUNC, 'a',
             ['x'],
             (Token.BLOCK, [
                 (Token.RETURN, (Token.EXPR, [
                     (Token.ASSIGN, None, (Token.OPEXPR, [(Token.MEMBER, (Token.ID, 'x'), None, None)]), None)
                 ])
                  )
             ])),
            (Token.FUNC, 'b',
             ['x'],
             (Token.BLOCK, [
                 (Token.RETURN, (Token.EXPR, [
                     (Token.ASSIGN, None, (Token.OPEXPR, [(Token.MEMBER, (Token.ID, 'x'), None, None)]), None)
                 ])
                  )
             ])),
            (Token.FUNC, 'c',
             [],
             (Token.BLOCK, [
                 (Token.RETURN, (Token.EXPR, [
                     (Token.ASSIGN, None, (Token.OPEXPR, [
                         (Token.MEMBER, (Token.ARRAY, [
                             (Token.ASSIGN, None, (Token.OPEXPR, [
                                 (Token.MEMBER, (Token.ID, 'a'), None, None)]), None),
                             (Token.ASSIGN, None, (Token.OPEXPR, [
                                 (Token.MEMBER, (Token.ID, 'b'), None, None)]), None)
                         ]), None, (Token.ELEM, (Token.EXPR, [
                              (Token.ASSIGN, None, (Token.OPEXPR, [(Token.MEMBER, (Token.INT, 0), None, None)]), None)
                         ]), (Token.CALL, [
                             (Token.ASSIGN, None, (Token.OPEXPR, [(Token.MEMBER, (Token.INT, 0), None, None)]), None)
                         ], None)))
                     ]), None)
                 ])
                  )
             ])),
        ]
        self.assertEqual(list(jsi.statements()), ast)

    def test_getfield(self):
        jsi = JSInterpreter('return a.var;', variables={'a': {'var': 3}})
        ast = [(Token.RETURN,
                (Token.EXPR, [
                    (Token.ASSIGN,
                     None,
                     (Token.OPEXPR, [
                         (Token.MEMBER,
                          (Token.ID, 'a'),
                          None,
                          (Token.FIELD, 'var', None)),
                     ]),
                     None)
                ]))
               ]
        self.assertEqual(list(jsi.statements()), ast)

    def test_if(self):
        jsi = JSInterpreter(
            '''
            function a(x) {
                if (x > 0)
                    return true;
                else
                    return false;
            }
            '''
        )
        ast = [
            (Token.FUNC, 'a',
             ['x'],
             (Token.BLOCK, [
                 (Token.IF,
                  (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                      (Token.MEMBER, (Token.ID, 'x'), None, None),
                      (Token.MEMBER, (Token.INT, 0), None, None),
                      (Token.REL, _RELATIONS['>'][1])
                  ]), None)]),
                  (Token.RETURN, (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                      (Token.MEMBER, (Token.BOOL, True), None, None)]), None)])),
                  (Token.RETURN, (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                      (Token.MEMBER, (Token.BOOL, False), None, None)]), None)])))

             ]))
        ]
        self.assertEqual(list(jsi.statements()), ast)

        jsi = JSInterpreter(
            '''
            function a(x) {
                if (x > 0)
                    return true;
                return false;
            }
            '''
        )
        ast = [
            (Token.FUNC, 'a',
             ['x'],
             (Token.BLOCK, [
                 (Token.IF,
                  (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                      (Token.MEMBER, (Token.ID, 'x'), None, None),
                      (Token.MEMBER, (Token.INT, 0), None, None),
                      (Token.REL, _RELATIONS['>'][1])
                  ]), None)]),
                  (Token.RETURN, (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                      (Token.MEMBER, (Token.BOOL, True), None, None)]), None)])),
                  None),
                 (Token.RETURN, (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                     (Token.MEMBER, (Token.BOOL, False), None, None)]), None)]))
             ]))
        ]
        self.assertEqual(list(jsi.statements()), ast)

        jsi = JSInterpreter(
            '''
            function a(x) {
                if (x > 0) {
                    x--;
                    return x;
                } else {
                    x++;
                    return x;
                }
            }
            '''
        )
        ast = [
            (Token.FUNC, 'a',
             ['x'],
             (Token.BLOCK, [
                 (Token.IF,
                  (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                      (Token.MEMBER, (Token.ID, 'x'), None, None),
                      (Token.MEMBER, (Token.INT, 0), None, None),
                      (Token.REL, _RELATIONS['>'][1])
                  ]), None)]),
                  (Token.BLOCK, [
                      (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                          (Token.MEMBER, (Token.ID, 'x'), None, None),
                          (Token.UOP, _UNARY_OPERATORS['--'][1])
                      ]), None)]),
                      (Token.RETURN, (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                          (Token.MEMBER, (Token.ID, 'x'), None, None)]), None)]))
                  ]),
                  (Token.BLOCK, [
                      (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                          (Token.MEMBER, (Token.ID, 'x'), None, None),
                          (Token.UOP, _UNARY_OPERATORS['++'][1])
                      ]), None)]),
                      (Token.RETURN, (Token.EXPR, [(Token.ASSIGN, None, (Token.OPEXPR, [
                          (Token.MEMBER, (Token.ID, 'x'), None, None)]), None)]))
                  ]))
             ]))
        ]
        self.assertEqual(list(jsi.statements()), ast)

    @unittest.skip('Test not yet implemented: missing code and ast')
    def test_with(self):
        # TODO with statement test
        jsi = JSInterpreter('')
        ast = []
        self.assertEqual(list(jsi.statements()), ast)

    @unittest.skip('Test not yet implemented: missing ast')
    def test_switch(self):
        # TODO switch statement test
        jsi = JSInterpreter(
            '''
            function a(x) {
                switch (x) {
                    case 6:
                        break;
                    case 5:
                        x++;
                    case 8:
                        x--;
                        break;
                    default:
                        x = 0;
                }
                return x;
            }
            '''
        )
        ast = []
        self.assertEqual(list(jsi.statements()), ast)

    @unittest.skip('Test not yet implemented: missing code and ast')
    def test_funct_expr(self):
        # TODO function expression test
        # might be combined with another
        jsi = JSInterpreter('')
        ast = []
        self.assertEqual(list(jsi.statements()), ast)

    @unittest.skip('Test not yet implemented: missing code and ast')
    def test_try(self):
        # TODO try statement test
        jsi = JSInterpreter('')
        ast = []
        self.assertEqual(list(jsi.statements()), ast)

    @unittest.skip('Test not yet implemented: missing code and ast')
    def test_throw(self):
        # TODO throw statement test
        # might be combined with another
        jsi = JSInterpreter('')
        ast = []
        self.assertEqual(list(jsi.statements()), ast)

    @unittest.skip('Test not yet implemented: missing code and ast')
    def test_label(self):
        # TODO label (break, continue) statement test
        # might be combined with another
        jsi = JSInterpreter('')
        ast = []
        self.assertEqual(list(jsi.statements()), ast)

    @unittest.skip('Test not yet implemented: missing code and ast')
    def test_debug(self):
        # TODO debugger statement test
        # might be combined with another
        jsi = JSInterpreter('')
        ast = []
        self.assertEqual(list(jsi.statements()), ast)

    def test_unshift(self):
        # https://hg.mozilla.org/mozilla-central/file/tip/js/src/tests/ecma_5/Array/unshift-01.js
        jsi = JSInterpreter(
            '''var MAX_LENGTH = 0xffffffff;

            var a = {};
            a.length = MAX_LENGTH + 1;
            assertEq([].unshift.call(a), MAX_LENGTH);
            assertEq(a.length, MAX_LENGTH);

            function testGetSet(len, expected) {
                var newlen;
                var a = { get length() { return len; }, set length(v) { newlen = v; } };
                var res = [].unshift.call(a);
                assertEq(res, expected);
                assertEq(newlen, expected);
            }

            testGetSet(0, 0);
            testGetSet(10, 10);
            testGetSet("1", 1);
            testGetSet(null, 0);
            testGetSet(MAX_LENGTH + 2, MAX_LENGTH);
            testGetSet(-5, 0);''')
        jsi.statements()

if __name__ == '__main__':
    unittest.main()
