from __future__ import unicode_literals

skip = {'parse': 'Ast not yet implemented'}

tests = [
    {
        'code': '"hello".split("");',
        'globals': {},
        'asserts': [{'value': ['h', 'e', 'l', 'l', 'o']}],
        'ast': []
    }
]
