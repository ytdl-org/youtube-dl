from __future__ import unicode_literals

from youtube_dl.jsinterp2.jsgrammar import Token

skip = {
    'jsinterp': 'Label statement is not supported',
    'interpret': 'Interpreting label not yet implemented',
        'parse': 'Test not yet implemented: missing code and ast'
}

tests = [
    {
        'code': '',
        'asserts': [{'value': 0}],
        'ast': []
    }
]
