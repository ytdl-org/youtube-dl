#!/usr/bin/env python

import sys
import unittest
import json

# Allow direct execution
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from youtube_dl.InfoExtractors import YoutubeUserIE, YoutubePlaylistIE, YoutubeIE
from youtube_dl.utils import *

PARAMETERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "parameters.json")
with io.open(PARAMETERS_FILE, encoding='utf-8') as pf:
    parameters = json.load(pf)

# General configuration (from __init__, not very elegant...)
jar = compat_cookiejar.CookieJar()
cookie_processor = compat_urllib_request.HTTPCookieProcessor(jar)
proxy_handler = compat_urllib_request.ProxyHandler()
opener = compat_urllib_request.build_opener(proxy_handler, cookie_processor, YoutubeDLHandler())
compat_urllib_request.install_opener(opener)

class FakeDownloader(object):
    def __init__(self):
        self.result = []
        self.params = parameters
    def to_screen(self, s):
        print(s)
    def trouble(self, s):
        raise Exception(s)
    def download(self, x):
        self.result.append(x)

class TestYoutubeLists(unittest.TestCase):
    def test_youtube_playlist(self):
        dl = FakeDownloader()
        ie = YoutubePlaylistIE(dl)
        ie.extract('https://www.youtube.com/playlist?list=PLwiyx1dc3P2JR9N8gQaQN_BCvlSlap7re')
        ytie_results = [YoutubeIE()._extract_id(r[0]) for r in dl.result]
        self.assertEqual(ytie_results, [ 'bV9L5Ht9LgY', 'FXxLjLQi3Fg', 'tU3Bgo5qJZE'])

    def test_issue_673(self):
        dl = FakeDownloader()
        ie = YoutubePlaylistIE(dl)
        ie.extract('PLBB231211A4F62143')
        self.assertTrue(len(dl.result) > 40)

    def test_youtube_playlist_long(self):
        dl = FakeDownloader()
        ie = YoutubePlaylistIE(dl)
        ie.extract('https://www.youtube.com/playlist?list=UUBABnxM4Ar9ten8Mdjj1j0Q')
        self.assertTrue(len(dl.result) >= 799)

    def test_youtube_playlist_with_deleted(self):
        #651
        dl = FakeDownloader()
        ie = YoutubePlaylistIE(dl)
        ie.extract('https://www.youtube.com/playlist?list=PLwP_SiAcdui0KVebT0mU9Apz359a4ubsC')
        ytie_results = [YoutubeIE()._extract_id(r[0]) for r in dl.result]
        self.assertFalse('pElCt5oNDuI' in ytie_results)
        self.assertFalse('KdPEApIVdWM' in ytie_results)

    def test_youtube_course(self):
        dl = FakeDownloader()
        ie = YoutubePlaylistIE(dl)
        # TODO find a > 100 (paginating?) videos course
        ie.extract('https://www.youtube.com/course?list=ECUl4u3cNGP61MdtwGTqZA0MreSaDybji8')
        self.assertEqual(YoutubeIE()._extract_id(dl.result[0][0]), 'j9WZyLZCBzs')
        self.assertEqual(len(dl.result), 25)
        self.assertEqual(YoutubeIE()._extract_id(dl.result[-1][0]), 'rYefUsYuEp0')

    def test_youtube_channel(self):
        # I give up, please find a channel that does paginate and test this like test_youtube_playlist_long
        pass # TODO

    def test_youtube_user(self):
        dl = FakeDownloader()
        ie = YoutubeUserIE(dl)
        ie.extract('https://www.youtube.com/user/TheLinuxFoundation')
        self.assertTrue(len(dl.result) >= 320)

if __name__ == '__main__':
    unittest.main()
