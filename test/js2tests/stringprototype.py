from __future__ import unicode_literals

skip = {
    'jsinterp': 'String literals are not supported',
    'parse': 'Ast not yet implemented'
}

tests = [
    {
        'exclude': ('jsinterp2',),
        'code': 'function f() {return "hello".split(""); }',
        'globals': {},
        'asserts': [{'value': ['h', 'e', 'l', 'l', 'o'], 'call': ('f',)}],
        'ast': []
    }
]
