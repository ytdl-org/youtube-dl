from __future__ import unicode_literals

from youtube_dl.jsinterp2.jsgrammar import TokenTypes

skip = {
    'jsinterp': 'Try statement is not supported',
    'interpret': 'Interpreting try statement is not yet implemented',
    'parse': 'Test is not yet implemented: missing code and ast'
}

tests = [
    {
        'code': '',
        'asserts': [{'value': 0}],
        'ast': []
    }
]
