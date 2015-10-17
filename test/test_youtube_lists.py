#!/usr/bin/env python
from __future__ import unicode_literals

# Allow direct execution
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test.helper import FakeYDL


from youtube_dl.extractor import (
    gen_extractors,
    YoutubePlaylistIE,
    YoutubeIE,
)


class TestYoutubeLists(unittest.TestCase):
    ies = gen_extractors()

    def assertIsPlaylist(self, info):
        """Make sure the info has '_type' set to 'playlist'"""
        self.assertEqual(info['_type'], 'playlist')

    def assertPlaylistHasVideos(self, playlist_url, videos):
        """Assert that playlist contains the given videos with matching IDs
        and titles.

        playlist_url:   Playlist URL
        videos:         List of dicts with the following entries:
                            "id":    Video ID
                            "title": Video title
        """

        # Get suitable InfoExtractor
        ie = [ie for ie in self.ies if ie.suitable(playlist_url)][0]

        # This results in "TypeError: 'YoutubeUserIE' object is
        # not callable", so it's necessary to use the
        # "ie.set_downloader(FakeYDL())" workaround.
        # YoutubeUserIE inherits from YoutubeChannelIE, which
        # inherits from InfoExtractor, which is callable, but it
        # doesn't work.  Even making YoutubeChannelIE inherit from
        # YoutubeBaseInfoExtractor doesn't make YoutubeUserIE
        # callable here.

        # ie = ie(FakeYDL())
        ie.set_downloader(FakeYDL())

        # Get playlist
        result = ie._real_extract(playlist_url)
        if result['_type'] == 'url':
            # Get actual playlist from canonical URL
            result = YoutubePlaylistIE(FakeYDL()).extract(result['url'])

        # Save generator output
        playlist = [v for v in result['entries']]

        # Find videos in playlist
        for video in videos:
            matching_videos = [v for v in playlist if v['id'] == video['id']]

            self.assertEqual(len(matching_videos), 1)
            self.assertEqual(matching_videos[0]['title'], video['title'])

        # TODO: It would be good to check that the videos are returned
        # in the correct order (not necessarily back-to-back), which,
        # of course, requires creating the test data in the correct
        # order. The reason is that simple mistakes (like forgetting
        # that dicts don't keep insertion order) can result in the
        # order being wrong. This could be in a separate test, or it
        # could go here.

    def test_youtube_playlist_noplaylist(self):
        dl = FakeYDL()
        dl.params['noplaylist'] = True
        ie = YoutubePlaylistIE(dl)
        result = ie.extract('https://www.youtube.com/watch?v=FXxLjLQi3Fg&list=PLwiyx1dc3P2JR9N8gQaQN_BCvlSlap7re')
        self.assertEqual(result['_type'], 'url')
        self.assertEqual(YoutubeIE().extract_id(result['url']), 'FXxLjLQi3Fg')

    def test_youtube_course(self):
        dl = FakeYDL()
        ie = YoutubePlaylistIE(dl)
        # TODO find a > 100 (paginating?) videos course
        result = ie.extract('https://www.youtube.com/course?list=ECUl4u3cNGP61MdtwGTqZA0MreSaDybji8')
        entries = result['entries']
        self.assertEqual(YoutubeIE().extract_id(entries[0]['url']), 'j9WZyLZCBzs')
        self.assertEqual(len(entries), 25)
        self.assertEqual(YoutubeIE().extract_id(entries[-1]['url']), 'rYefUsYuEp0')

    def test_youtube_mix(self):
        dl = FakeYDL()
        ie = YoutubePlaylistIE(dl)
        result = ie.extract('https://www.youtube.com/watch?v=W01L70IGBgE&index=2&list=RDOQpdSVF_k_w')
        entries = result['entries']
        self.assertTrue(len(entries) >= 20)
        original_video = entries[0]
        self.assertEqual(original_video['id'], 'OQpdSVF_k_w')

    def test_youtube_toptracks(self):
        print('Skipping: The playlist page gives error 500')
        return
        dl = FakeYDL()
        ie = YoutubePlaylistIE(dl)
        result = ie.extract('https://www.youtube.com/playlist?list=MCUS')
        entries = result['entries']
        self.assertEqual(len(entries), 100)

    def test_youtube_extract_video_titles_from_playlists(self):
        self.assertPlaylistHasVideos("https://www.youtube.com/user/RhettandLink/videos",
                                     [
                                         {'id': 'uhKejRHODOM', 'title': 'The Overly Complicated Coffee Order'},
                                         {'id': 'f7eIWlA6Sh8', 'title': 'Burgaz Megatator Commercial'}
                                     ])
        self.assertPlaylistHasVideos("https://www.youtube.com/playlist?list=PLJ49NV73ttrvgyM4n5o-txRnMXH3pNnjK",
                                     [
                                         {'id': 'x9CH3RtbW_M', 'title': 'The Secret Life of a Hamster Song - Animated Song Biscuits'}
                                     ])

if __name__ == '__main__':
    unittest.main()
