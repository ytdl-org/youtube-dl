#!/usr/bin/env python

import sys
import unittest

# Allow direct execution
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from youtube_dl.InfoExtractors import JustinTVIE

class TestJustinTVMatching(unittest.TestCase):
    def test_justin_tv_channelid_matching(self):
        self.assertTrue(JustinTVIE.suitable(u"justin.tv/vanillatv"))
        self.assertTrue(JustinTVIE.suitable(u"twitch.tv/vanillatv"))
        self.assertTrue(JustinTVIE.suitable(u"www.justin.tv/vanillatv"))
        self.assertTrue(JustinTVIE.suitable(u"www.twitch.tv/vanillatv"))
        self.assertTrue(JustinTVIE.suitable(u"http://www.justin.tv/vanillatv"))
        self.assertTrue(JustinTVIE.suitable(u"http://www.twitch.tv/vanillatv"))
        self.assertTrue(JustinTVIE.suitable(u"http://www.justin.tv/vanillatv/"))
        self.assertTrue(JustinTVIE.suitable(u"http://www.twitch.tv/vanillatv/"))

    def test_justintv_videoid_matching(self):
        self.assertTrue(JustinTVIE.suitable(u"http://www.twitch.tv/vanillatv/b/328087483"))

    def test_justin_tv_chapterid_matching(self):
        self.assertTrue(JustinTVIE.suitable(u"http://www.twitch.tv/tsm_theoddone/c/2349361"))

if __name__ == '__main__':
    unittest.main()
