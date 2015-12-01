#!/usr/bin/env python
from __future__ import unicode_literals

# Allow direct execution
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from itertools import repeat

from youtube_dl.options import parseOpts

URL = 'someurl'

class TestOptions(unittest.TestCase):

    def test_multiple_titles(self):
        # test that parser will accept multiple reject-title and match-title options
        regexes = ['regex' + i for i in map(str, range(10))]
        for name in ['reject', 'match']:
            options = [x for opts in zip(repeat('--' + name + '-title'), regexes) for x in opts]
            parser, opts, args = parseOpts(options + [URL])
            self.assertEqual(getattr(opts, name + 'title'), regexes)


if __name__ == '__main__':
    unittest.main()
