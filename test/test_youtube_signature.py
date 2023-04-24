#!/usr/bin/env python

from __future__ import unicode_literals

# Allow direct execution
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import io
import re
import string

from youtube_dl.compat import compat_str, compat_urlretrieve

from test.helper import FakeYDL
from youtube_dl.extractor import YoutubeIE
from youtube_dl.jsinterp import JSInterpreter

_SIG_TESTS = [
    (
        'https://s.ytimg.com/yts/jsbin/html5player-vflHOr_nV.js',
        86,
        '>=<;:/.-[+*)(\'&%$#"!ZYX0VUTSRQPONMLKJIHGFEDCBA\\yxwvutsrqponmlkjihgfedcba987654321',
    ),
    (
        'https://s.ytimg.com/yts/jsbin/html5player-vfldJ8xgI.js',
        85,
        '3456789a0cdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRS[UVWXYZ!"#$%&\'()*+,-./:;<=>?@',
    ),
    (
        'https://s.ytimg.com/yts/jsbin/html5player-vfle-mVwz.js',
        90,
        ']\\[@?>=<;:/.-,+*)(\'&%$#"hZYXWVUTSRQPONMLKJIHGFEDCBAzyxwvutsrqponmlkjiagfedcb39876',
    ),
    (
        'https://s.ytimg.com/yts/jsbin/html5player-en_US-vfl0Cbn9e.js',
        84,
        'O1I3456789abcde0ghijklmnopqrstuvwxyzABCDEFGHfJKLMN2PQRSTUVW@YZ!"#$%&\'()*+,-./:;<=',
    ),
    (
        'https://s.ytimg.com/yts/jsbin/html5player-en_US-vflXGBaUN.js',
        '2ACFC7A61CA478CD21425E5A57EBD73DDC78E22A.2094302436B2D377D14A3BBA23022D023B8BC25AA',
        'A52CB8B320D22032ABB3A41D773D2B6342034902.A22E87CDD37DBE75A5E52412DC874AC16A7CFCA2',
    ),
    (
        'https://s.ytimg.com/yts/jsbin/html5player-en_US-vflBb0OQx.js',
        84,
        '123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQ0STUVWXYZ!"#$%&\'()*+,@./:;<=>'
    ),
    (
        'https://s.ytimg.com/yts/jsbin/html5player-en_US-vfl9FYC6l.js',
        83,
        '123456789abcdefghijklmnopqr0tuvwxyzABCDETGHIJKLMNOPQRS>UVWXYZ!"#$%&\'()*+,-./:;<=F'
    ),
    (
        'https://s.ytimg.com/yts/jsbin/html5player-en_US-vflCGk6yw/html5player.js',
        '4646B5181C6C3020DF1D9C7FCFEA.AD80ABF70C39BD369CCCAE780AFBB98FA6B6CB42766249D9488C288',
        '82C8849D94266724DC6B6AF89BBFA087EACCD963.B93C07FBA084ACAEFCF7C9D1FD0203C6C1815B6B'
    ),
    (
        'https://s.ytimg.com/yts/jsbin/html5player-en_US-vflKjOTVq/html5player.js',
        '312AA52209E3623129A412D56A40F11CB0AF14AE.3EE09501CB14E3BCDC3B2AE808BF3F1D14E7FBF12',
        '112AA5220913623229A412D56A40F11CB0AF14AE.3EE0950FCB14EEBCDC3B2AE808BF331D14E7FBF3',
    )
]

_NSIG_TESTS = [
    (
        'https://www.youtube.com/s/player/7862ca1f/player_ias.vflset/en_US/base.js',
        'X_LCxVDjAavgE5t', 'yxJ1dM6iz5ogUg',
    ),
    (
        'https://www.youtube.com/s/player/9216d1f7/player_ias.vflset/en_US/base.js',
        'SLp9F5bwjAdhE9F-', 'gWnb9IK2DJ8Q1w',
    ),
    (
        'https://www.youtube.com/s/player/f8cb7a3b/player_ias.vflset/en_US/base.js',
        'oBo2h5euWy6osrUt', 'ivXHpm7qJjJN',
    ),
    (
        'https://www.youtube.com/s/player/2dfe380c/player_ias.vflset/en_US/base.js',
        'oBo2h5euWy6osrUt', '3DIBbn3qdQ',
    ),
    (
        'https://www.youtube.com/s/player/f1ca6900/player_ias.vflset/en_US/base.js',
        'cu3wyu6LQn2hse', 'jvxetvmlI9AN9Q',
    ),
    (
        'https://www.youtube.com/s/player/8040e515/player_ias.vflset/en_US/base.js',
        'wvOFaY-yjgDuIEg5', 'HkfBFDHmgw4rsw',
    ),
    (
        'https://www.youtube.com/s/player/e06dea74/player_ias.vflset/en_US/base.js',
        'AiuodmaDDYw8d3y4bf', 'ankd8eza2T6Qmw',
    ),
    (
        'https://www.youtube.com/s/player/5dd88d1d/player-plasma-ias-phone-en_US.vflset/base.js',
        'kSxKFLeqzv_ZyHSAt', 'n8gS8oRlHOxPFA',
    ),
    (
        'https://www.youtube.com/s/player/324f67b9/player_ias.vflset/en_US/base.js',
        'xdftNy7dh9QGnhW', '22qLGxrmX8F1rA',
    ),
    (
        'https://www.youtube.com/s/player/4c3f79c5/player_ias.vflset/en_US/base.js',
        'TDCstCG66tEAO5pR9o', 'dbxNtZ14c-yWyw',
    ),
    (
        'https://www.youtube.com/s/player/c81bbb4a/player_ias.vflset/en_US/base.js',
        'gre3EcLurNY2vqp94', 'Z9DfGxWP115WTg',
    ),
    (
        'https://www.youtube.com/s/player/1f7d5369/player_ias.vflset/en_US/base.js',
        'batNX7sYqIJdkJ', 'IhOkL_zxbkOZBw',
    ),
    (
        'https://www.youtube.com/s/player/009f1d77/player_ias.vflset/en_US/base.js',
        '5dwFHw8aFWQUQtffRq', 'audescmLUzI3jw',
    ),
    (
        'https://www.youtube.com/s/player/dc0c6770/player_ias.vflset/en_US/base.js',
        '5EHDMgYLV6HPGk_Mu-kk', 'n9lUJLHbxUI0GQ',
    ),
    (
        'https://www.youtube.com/s/player/c2199353/player_ias.vflset/en_US/base.js',
        '5EHDMgYLV6HPGk_Mu-kk', 'AD5rgS85EkrE7',
    ),
    (
        'https://www.youtube.com/s/player/113ca41c/player_ias.vflset/en_US/base.js',
        'cgYl-tlYkhjT7A', 'hI7BBr2zUgcmMg',
    ),
    (
        'https://www.youtube.com/s/player/c57c113c/player_ias.vflset/en_US/base.js',
        '-Txvy6bT5R6LqgnQNx', 'dcklJCnRUHbgSg',
    ),
    (
        'https://www.youtube.com/s/player/5a3b6271/player_ias.vflset/en_US/base.js',
        'B2j7f_UPT4rfje85Lu_e', 'm5DmNymaGQ5RdQ',
    ),
    (
        'https://www.youtube.com/s/player/dac945fd/player_ias.vflset/en_US/base.js',
        'o8BkRxXhuYsBCWi6RplPdP', '3Lx32v_hmzTm6A',
    ),
]


class TestPlayerInfo(unittest.TestCase):
    def test_youtube_extract_player_info(self):
        PLAYER_URLS = (
            ('https://www.youtube.com/s/player/4c3f79c5/player_ias.vflset/en_US/base.js', '4c3f79c5'),
            ('https://www.youtube.com/s/player/64dddad9/player_ias.vflset/en_US/base.js', '64dddad9'),
            ('https://www.youtube.com/s/player/64dddad9/player_ias.vflset/fr_FR/base.js', '64dddad9'),
            ('https://www.youtube.com/s/player/64dddad9/player-plasma-ias-phone-en_US.vflset/base.js', '64dddad9'),
            ('https://www.youtube.com/s/player/64dddad9/player-plasma-ias-phone-de_DE.vflset/base.js', '64dddad9'),
            ('https://www.youtube.com/s/player/64dddad9/player-plasma-ias-tablet-en_US.vflset/base.js', '64dddad9'),
            # obsolete
            ('https://www.youtube.com/yts/jsbin/player_ias-vfle4-e03/en_US/base.js', 'vfle4-e03'),
            ('https://www.youtube.com/yts/jsbin/player_ias-vfl49f_g4/en_US/base.js', 'vfl49f_g4'),
            ('https://www.youtube.com/yts/jsbin/player_ias-vflCPQUIL/en_US/base.js', 'vflCPQUIL'),
            ('https://www.youtube.com/yts/jsbin/player-vflzQZbt7/en_US/base.js', 'vflzQZbt7'),
            ('https://www.youtube.com/yts/jsbin/player-en_US-vflaxXRn1/base.js', 'vflaxXRn1'),
            ('https://s.ytimg.com/yts/jsbin/html5player-en_US-vflXGBaUN.js', 'vflXGBaUN'),
            ('https://s.ytimg.com/yts/jsbin/html5player-en_US-vflKjOTVq/html5player.js', 'vflKjOTVq'),
        )
        for player_url, expected_player_id in PLAYER_URLS:
            player_id = YoutubeIE._extract_player_info(player_url)
            self.assertEqual(player_id, expected_player_id)


class TestSignature(unittest.TestCase):
    def setUp(self):
        TEST_DIR = os.path.dirname(os.path.abspath(__file__))
        self.TESTDATA_DIR = os.path.join(TEST_DIR, 'testdata/sigs')
        if not os.path.exists(self.TESTDATA_DIR):
            os.mkdir(self.TESTDATA_DIR)

    def tearDown(self):
        try:
            for f in os.listdir(self.TESTDATA_DIR):
                os.remove(f)
        except OSError:
            pass


def t_factory(name, sig_func, url_pattern):
    def make_tfunc(url, sig_input, expected_sig):
        m = url_pattern.match(url)
        assert m, '%r should follow URL format' % url
        test_id = m.group('id')

        def test_func(self):
            basename = 'player-{0}-{1}.js'.format(name, test_id)
            fn = os.path.join(self.TESTDATA_DIR, basename)

            if not os.path.exists(fn):
                compat_urlretrieve(url, fn)
            with io.open(fn, encoding='utf-8') as testf:
                jscode = testf.read()
            self.assertEqual(sig_func(jscode, sig_input), expected_sig)

        test_func.__name__ = str('test_{0}_js_{1}'.format(name, test_id))
        setattr(TestSignature, test_func.__name__, test_func)
    return make_tfunc


def signature(jscode, sig_input):
    func = YoutubeIE(FakeYDL())._parse_sig_js(jscode)
    src_sig = (
        compat_str(string.printable[:sig_input])
        if isinstance(sig_input, int) else sig_input)
    return func(src_sig)


def n_sig(jscode, sig_input):
    funcname = YoutubeIE(FakeYDL())._extract_n_function_name(jscode)
    return JSInterpreter(jscode).call_function(funcname, sig_input)


make_sig_test = t_factory(
    'signature', signature, re.compile(r'.*-(?P<id>[a-zA-Z0-9_-]+)(?:/watch_as3|/html5player)?\.[a-z]+$'))
for test_spec in _SIG_TESTS:
    make_sig_test(*test_spec)

make_nsig_test = t_factory(
    'nsig', n_sig, re.compile(r'.+/player/(?P<id>[a-zA-Z0-9_-]+)/.+.js$'))
for test_spec in _NSIG_TESTS:
    make_nsig_test(*test_spec)


if __name__ == '__main__':
    unittest.main()
