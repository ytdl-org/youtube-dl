#!/usr/bin/env python

import sys
import unittest
import socket

# Allow direct execution
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from youtube_dl.InfoExtractors import YoutubePlaylistIE
from youtube_dl.utils import *

# General configuration (from __init__, not very elegant...)
jar = compat_cookiejar.CookieJar()
cookie_processor = compat_urllib_request.HTTPCookieProcessor(jar)
proxy_handler = compat_urllib_request.ProxyHandler()
opener = compat_urllib_request.build_opener(proxy_handler, cookie_processor, YoutubeDLHandler())
compat_urllib_request.install_opener(opener)
socket.setdefaulttimeout(300) # 5 minutes should be enough (famous last words)

class FakeDownloader(object):
    def __init__(self):
        self.result = []
        self.params = {}
    def to_screen(self, s):
        print(s)
    def trouble(self, s):
        raise Exception(s)
    def download(self, x):
        self.result.append(x)

class TestYoutubeLists(unittest.TestCase):
    def test_youtube_playlist(self):
        DL = FakeDownloader()
        IE = YoutubePlaylistIE(DL)
        IE.extract('https://www.youtube.com/playlist?list=PLwiyx1dc3P2JR9N8gQaQN_BCvlSlap7re')
        self.assertEqual(DL.result, [
            ['http://www.youtube.com/watch?v=bV9L5Ht9LgY'],
            ['http://www.youtube.com/watch?v=FXxLjLQi3Fg'],
            ['http://www.youtube.com/watch?v=tU3Bgo5qJZE']
        ])

    def test_youtube_playlist_long(self):
        DL = FakeDownloader()
        IE = YoutubePlaylistIE(DL)
        IE.extract('https://www.youtube.com/playlist?list=UUBABnxM4Ar9ten8Mdjj1j0Q')
        self.assertTrue(len(DL.result) >= 799)

    def test_youtube_course(self):
        DL = FakeDownloader()
        IE = YoutubePlaylistIE(DL)
        # TODO find a > 100 (paginating?) videos course
        IE.extract('https://www.youtube.com/course?list=ECUl4u3cNGP61MdtwGTqZA0MreSaDybji8')
        self.assertEqual(DL.result[0], ['http://www.youtube.com/watch?v=j9WZyLZCBzs'])
        self.assertEqual(len(DL.result), 25)
        self.assertEqual(DL.result[-1], ['http://www.youtube.com/watch?v=rYefUsYuEp0'])

    def test_youtube_channel(self):
        """I give up, please find a channel that does paginate and test this like test_youtube_playlist_long"""
        pass # TODO

    def test_youtube_user(self):
        DL = FakeDownloader()
        IE = YoutubePlaylistIE(DL)
        IE.extract('https://www.youtube.com/user/TheLinuxFoundation')
        self.assertTrue(len(DL.result) >= 320)

if __name__ == '__main__':
    unittest.main()
