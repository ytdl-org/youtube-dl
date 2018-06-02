from __future__ import unicode_literals

skip = {
    'jsinterp': 'Unary opertations are not supported',
    'parse': True
}

tests = [
    {
        'code': 'function f() { return -5 + +3; }',
        'asserts': [{'value': -2, 'call': ('f',)}]
    }, {
        'code': 'function f() {return -5 + ++a;}',
        'globals': {'a': -3},
        'asserts': [{'value': -7, 'call': ('f',)}, {'value': -6, 'call': ('f',)}]
    }, {
        'code': 'function f() {return -5 + a++;}',
        'globals': {'a': -3},
        'asserts': [{'value': -8, 'call': ('f',)}, {'value': -7, 'call': ('f',)}]
    }
]
