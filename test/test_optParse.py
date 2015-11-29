#!/usr/bin/env python
from __future__ import unicode_literals

# Allow direct execution
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from youtube_dl.options.options_argparse import parseOpts

from itertools import repeat

# Jimquesition
URL = 'https://www.youtube.com/watch?v=DpG4t54g2fk'

class TestOptionParser(unittest.TestCase):

    def test(self):
        #import pdb; pdb.set_trace()
        with self.assertRaises(SystemExit):
            backup = sys.stdout
            sys.stdout = StringIO()
            parseOpts(['--help'])
            sys.stdout = backup

    def test_multiple_regex_patterns(self):
        # no patterns given
        parser, args, args = parseOpts([URL])
        self.assertIs(args.rejecttitle, None)
        self.assertIs(args.matchtitle, None)

        #sys.stdout = sys.stderr

        regexes = [ 'REGEX' + str(i) for i in range(10) ]
        def getargs(option):
            "return [ option, regex[0], option, regex[1], option, regex[N] ]"
            return [x for t in zip(repeat(option), regexes) for x in t] + [URL]

        args = getargs('--reject-title')
        parser, args, args = parseOpts(args)
        self.assertListEqual(args.rejecttitle, regexes)

        args = getargs('--match-title')
        parser, args, args = parseOpts(args)
        self.assertListEqual(args.matchtitle, regexes)


if __name__ == '__main__':
    unittest.main()
