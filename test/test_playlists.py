#!/usr/bin/env python
# encoding: utf-8


# Allow direct execution
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test.helper import FakeYDL, global_setup
global_setup()


from youtube_dl.extractor import (
    DailymotionPlaylistIE,
    DailymotionUserIE,
    VimeoChannelIE,
    UstreamChannelIE,
    SoundcloudSetIE,
    SoundcloudUserIE,
    LivestreamIE,
    NHLVideocenterIE,
    BambuserChannelIE,
    BandcampAlbumIE
)


class TestPlaylists(unittest.TestCase):
    def assertIsPlaylist(self, info):
        """Make sure the info has '_type' set to 'playlist'"""
        self.assertEqual(info['_type'], 'playlist')

    def test_dailymotion_playlist(self):
        dl = FakeYDL()
        ie = DailymotionPlaylistIE(dl)
        result = ie.extract('http://www.dailymotion.com/playlist/xv4bw_nqtv_sport/1#video=xl8v3q')
        self.assertIsPlaylist(result)
        self.assertEqual(result['title'], u'SPORT')
        self.assertTrue(len(result['entries']) > 20)

    def test_dailymotion_user(self):
        dl = FakeYDL()
        ie = DailymotionUserIE(dl)
        result = ie.extract('http://www.dailymotion.com/user/generation-quoi/')
        self.assertIsPlaylist(result)
        self.assertEqual(result['title'], u'Génération Quoi')
        self.assertTrue(len(result['entries']) >= 26)

    def test_vimeo_channel(self):
        dl = FakeYDL()
        ie = VimeoChannelIE(dl)
        result = ie.extract('http://vimeo.com/channels/tributes')
        self.assertIsPlaylist(result)
        self.assertEqual(result['title'], u'Vimeo Tributes')
        self.assertTrue(len(result['entries']) > 24)

    def test_ustream_channel(self):
        dl = FakeYDL()
        ie = UstreamChannelIE(dl)
        result = ie.extract('http://www.ustream.tv/channel/young-americans-for-liberty')
        self.assertIsPlaylist(result)
        self.assertEqual(result['id'], u'5124905')
        self.assertTrue(len(result['entries']) >= 11)

    def test_soundcloud_set(self):
        dl = FakeYDL()
        ie = SoundcloudSetIE(dl)
        result = ie.extract('https://soundcloud.com/the-concept-band/sets/the-royal-concept-ep')
        self.assertIsPlaylist(result)
        self.assertEqual(result['title'], u'The Royal Concept EP')
        self.assertTrue(len(result['entries']) >= 6)

    def test_soundcloud_user(self):
        dl = FakeYDL()
        ie = SoundcloudUserIE(dl)
        result = ie.extract('https://soundcloud.com/the-concept-band')
        self.assertIsPlaylist(result)
        self.assertEqual(result['id'], u'9615865')
        self.assertTrue(len(result['entries']) >= 12)

    def test_livestream_event(self):
        dl = FakeYDL()
        ie = LivestreamIE(dl)
        result = ie.extract('http://new.livestream.com/tedx/cityenglish')
        self.assertIsPlaylist(result)
        self.assertEqual(result['title'], u'TEDCity2.0 (English)')
        self.assertTrue(len(result['entries']) >= 4)

    def test_nhl_videocenter(self):
        dl = FakeYDL()
        ie = NHLVideocenterIE(dl)
        result = ie.extract('http://video.canucks.nhl.com/videocenter/console?catid=999')
        self.assertIsPlaylist(result)
        self.assertEqual(result['id'], u'999')
        self.assertEqual(result['title'], u'Highlights')
        self.assertEqual(len(result['entries']), 12)

    def test_bambuser_channel(self):
        dl = FakeYDL()
        ie = BambuserChannelIE(dl)
        result = ie.extract('http://bambuser.com/channel/pixelversity')
        self.assertIsPlaylist(result)
        self.assertEqual(result['title'], u'pixelversity')
        self.assertTrue(len(result['entries']) >= 66)

    def test_bandcamp_album(self):
        dl = FakeYDL()
        ie = BandcampAlbumIE(dl)
        result = ie.extract('http://mpallante.bandcamp.com/album/nightmare-night-ep')
        self.assertIsPlaylist(result)
        self.assertEqual(result['title'], u'Nightmare Night EP')
        self.assertTrue(len(result['entries']) >= 4)

if __name__ == '__main__':
    unittest.main()
