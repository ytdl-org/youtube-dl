#!/usr/bin/env python

# Allow direct execution
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


import io
import re
import string

from youtube_dl.extractor import YoutubeIE
from youtube_dl.utils import compat_str, compat_urlretrieve

_TESTS = [
    (
        u'https://s.ytimg.com/yts/jsbin/html5player-vflHOr_nV.js',
        u'js',
        86,
        u'>=<;:/.-[+*)(\'&%$#"!ZYX0VUTSRQPONMLKJIHGFEDCBA\\yxwvutsrqponmlkjihgfedcba987654321',
    ),
    (
        u'https://s.ytimg.com/yts/jsbin/html5player-vfldJ8xgI.js',
        u'js',
        85,
        u'3456789a0cdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRS[UVWXYZ!"#$%&\'()*+,-./:;<=>?@',
    ),
    (
        u'https://s.ytimg.com/yts/jsbin/html5player-vfle-mVwz.js',
        u'js',
        90,
        u']\\[@?>=<;:/.-,+*)(\'&%$#"hZYXWVUTSRQPONMLKJIHGFEDCBAzyxwvutsrqponmlkjiagfedcb39876',
    ),
    (
        u'https://s.ytimg.com/yts/jsbin/html5player-en_US-vflXGBaUN.js',
        u'js',
        u'BF51B8F76F05D81CEAED01F5ACE376131B23D830.5805F8368CB04C36C973A8CF997B774AC4B685B77',
        u'2909FDCA8C5E6D92D34B34E7C7AFFD7CA57532DA.5BA2848AD58DAA15002012C7CD77187D24E048A5',
    ),
]


class TestSignature(unittest.TestCase):
    def setUp(self):
        TEST_DIR = os.path.dirname(os.path.abspath(__file__))
        self.TESTDATA_DIR = os.path.join(TEST_DIR, 'testdata')
        if not os.path.exists(self.TESTDATA_DIR):
            os.mkdir(self.TESTDATA_DIR)


def make_tfunc(url, stype, sig_input, expected_sig):
    basename = url.rpartition('/')[2]
    m = re.match(r'.*-([a-zA-Z0-9_-]+)\.[a-z]+$', basename)
    assert m, '%r should follow URL format' % basename
    test_id = m.group(1)

    def test_func(self):
        fn = os.path.join(self.TESTDATA_DIR, basename)

        if not os.path.exists(fn):
            compat_urlretrieve(url, fn)

        ie = YoutubeIE()
        if stype == 'js':
            with io.open(fn, encoding='utf-8') as testf:
                jscode = testf.read()
            func = ie._parse_sig_js(jscode)
        else:
            assert stype == 'swf'
            with open(fn, 'rb') as testf:
                swfcode = testf.read()
            func = ie._parse_sig_swf(swfcode)
        src_sig = (
            compat_str(string.printable[:sig_input])
            if isinstance(sig_input, int) else sig_input)
        got_sig = func(src_sig)
        self.assertEqual(got_sig, expected_sig)

    test_func.__name__ = str('test_signature_' + stype + '_' + test_id)
    setattr(TestSignature, test_func.__name__, test_func)

for test_spec in _TESTS:
    make_tfunc(*test_spec)


if __name__ == '__main__':
    unittest.main()
