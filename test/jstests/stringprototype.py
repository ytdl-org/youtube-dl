from __future__ import unicode_literals

skip = {
    'jsinterp': 'String literals are not supported',
    'parse': 'Test is not yet implemented: missing ast'
}

tests = [
    {
        'code': 'function f() {return "hello".split(""); }',
        'globals': {},
        'asserts': [{'value': ['h', 'e', 'l', 'l', 'o'], 'call': ('f',)}],
        'ast': []
    }
]
