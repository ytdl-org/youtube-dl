from __future__ import unicode_literals

from youtube_dl.jsinterp2.jsgrammar import Token

skip = {
    'jsinterp': 'With statement is not supported',
    'interpret': 'Interpreting with statement is not yet implemented',
    'parse': 'Test is not yet implemented: missing code and ast'
}

tests = [
    {
        'code': '',
        'asserts': [{'value': 0}],
        'ast': []
    }
]
