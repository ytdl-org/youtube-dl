from __future__ import unicode_literals

from youtube_dl.jsinterp2.jsgrammar import Token

skip = {
    'jsinterp': 'Debugger statement is not supported',
    'interpret': 'Interpreting debugger statement is not yet implemented',
    'parse': 'Test is not yet implemented: missing code and ast'
}

tests = [
    {
        'code': '',
        'asserts': [{'value': 0}],
        'ast': []
    }
]
