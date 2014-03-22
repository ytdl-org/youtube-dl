#!/usr/bin/env python
# encoding: utf-8

from __future__ import unicode_literals

# Allow direct execution
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test.helper import FakeYDL


from youtube_dl.extractor import (
    AcademicEarthCourseIE,
    DailymotionPlaylistIE,
    DailymotionUserIE,
    VimeoChannelIE,
    VimeoUserIE,
    VimeoAlbumIE,
    VimeoGroupsIE,
    UstreamChannelIE,
    SoundcloudSetIE,
    SoundcloudUserIE,
    LivestreamIE,
    NHLVideocenterIE,
    BambuserChannelIE,
    BandcampAlbumIE,
    SmotriCommunityIE,
    SmotriUserIE,
    IviCompilationIE,
    ImdbListIE,
    KhanAcademyIE,
    EveryonesMixtapeIE,
    RutubeChannelIE,
    GoogleSearchIE,
    GenericIE,
    TEDIE,
    ToypicsUserIE,
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
        self.assertEqual(result['title'], 'SPORT')
        self.assertTrue(len(result['entries']) > 20)

    def test_dailymotion_user(self):
        dl = FakeYDL()
        ie = DailymotionUserIE(dl)
        result = ie.extract('https://www.dailymotion.com/user/nqtv')
        self.assertIsPlaylist(result)
        self.assertEqual(result['title'], 'Rémi Gaillard')
        self.assertTrue(len(result['entries']) >= 100)

    def test_vimeo_channel(self):
        dl = FakeYDL()
        ie = VimeoChannelIE(dl)
        result = ie.extract('http://vimeo.com/channels/tributes')
        self.assertIsPlaylist(result)
        self.assertEqual(result['title'], 'Vimeo Tributes')
        self.assertTrue(len(result['entries']) > 24)

    def test_vimeo_user(self):
        dl = FakeYDL()
        ie = VimeoUserIE(dl)
        result = ie.extract('http://vimeo.com/nkistudio/videos')
        self.assertIsPlaylist(result)
        self.assertEqual(result['title'], 'Nki')
        self.assertTrue(len(result['entries']) > 65)

    def test_vimeo_album(self):
        dl = FakeYDL()
        ie = VimeoAlbumIE(dl)
        result = ie.extract('http://vimeo.com/album/2632481')
        self.assertIsPlaylist(result)
        self.assertEqual(result['title'], 'Staff Favorites: November 2013')
        self.assertTrue(len(result['entries']) > 12)

    def test_vimeo_groups(self):
        dl = FakeYDL()
        ie = VimeoGroupsIE(dl)
        result = ie.extract('http://vimeo.com/groups/rolexawards')
        self.assertIsPlaylist(result)
        self.assertEqual(result['title'], 'Rolex Awards for Enterprise')
        self.assertTrue(len(result['entries']) > 72)

    def test_ustream_channel(self):
        dl = FakeYDL()
        ie = UstreamChannelIE(dl)
        result = ie.extract('http://www.ustream.tv/channel/young-americans-for-liberty')
        self.assertIsPlaylist(result)
        self.assertEqual(result['id'], '5124905')
        self.assertTrue(len(result['entries']) >= 6)

    def test_soundcloud_set(self):
        dl = FakeYDL()
        ie = SoundcloudSetIE(dl)
        result = ie.extract('https://soundcloud.com/the-concept-band/sets/the-royal-concept-ep')
        self.assertIsPlaylist(result)
        self.assertEqual(result['title'], 'The Royal Concept EP')
        self.assertTrue(len(result['entries']) >= 6)

    def test_soundcloud_user(self):
        dl = FakeYDL()
        ie = SoundcloudUserIE(dl)
        result = ie.extract('https://soundcloud.com/the-concept-band')
        self.assertIsPlaylist(result)
        self.assertEqual(result['id'], '9615865')
        self.assertTrue(len(result['entries']) >= 12)

    def test_livestream_event(self):
        dl = FakeYDL()
        ie = LivestreamIE(dl)
        result = ie.extract('http://new.livestream.com/tedx/cityenglish')
        self.assertIsPlaylist(result)
        self.assertEqual(result['title'], 'TEDCity2.0 (English)')
        self.assertTrue(len(result['entries']) >= 4)

    def test_nhl_videocenter(self):
        dl = FakeYDL()
        ie = NHLVideocenterIE(dl)
        result = ie.extract('http://video.canucks.nhl.com/videocenter/console?catid=999')
        self.assertIsPlaylist(result)
        self.assertEqual(result['id'], '999')
        self.assertEqual(result['title'], 'Highlights')
        self.assertEqual(len(result['entries']), 12)

    def test_bambuser_channel(self):
        dl = FakeYDL()
        ie = BambuserChannelIE(dl)
        result = ie.extract('http://bambuser.com/channel/pixelversity')
        self.assertIsPlaylist(result)
        self.assertEqual(result['title'], 'pixelversity')
        self.assertTrue(len(result['entries']) >= 60)

    def test_bandcamp_album(self):
        dl = FakeYDL()
        ie = BandcampAlbumIE(dl)
        result = ie.extract('http://mpallante.bandcamp.com/album/nightmare-night-ep')
        self.assertIsPlaylist(result)
        self.assertEqual(result['title'], 'Nightmare Night EP')
        self.assertTrue(len(result['entries']) >= 4)
        
    def test_smotri_community(self):
        dl = FakeYDL()
        ie = SmotriCommunityIE(dl)
        result = ie.extract('http://smotri.com/community/video/kommuna')
        self.assertIsPlaylist(result)
        self.assertEqual(result['id'], 'kommuna')
        self.assertEqual(result['title'], 'КПРФ')
        self.assertTrue(len(result['entries']) >= 4)
        
    def test_smotri_user(self):
        dl = FakeYDL()
        ie = SmotriUserIE(dl)
        result = ie.extract('http://smotri.com/user/inspector')
        self.assertIsPlaylist(result)
        self.assertEqual(result['id'], 'inspector')
        self.assertEqual(result['title'], 'Inspector')
        self.assertTrue(len(result['entries']) >= 9)

    def test_AcademicEarthCourse(self):
        dl = FakeYDL()
        ie = AcademicEarthCourseIE(dl)
        result = ie.extract('http://academicearth.org/playlists/laws-of-nature/')
        self.assertIsPlaylist(result)
        self.assertEqual(result['id'], 'laws-of-nature')
        self.assertEqual(result['title'], 'Laws of Nature')
        self.assertEqual(result['description'],u'Introduce yourself to the laws of nature with these free online college lectures from Yale, Harvard, and MIT.')# u"Today's websites are increasingly dynamic. Pages are no longer static HTML files but instead generated by scripts and database calls. User interfaces are more seamless, with technologies like Ajax replacing traditional page reloads. This course teaches students how to build dynamic websites with Ajax and with Linux, Apache, MySQL, and PHP (LAMP), one of today's most popular frameworks. Students learn how to set up domain names with DNS, how to structure pages with XHTML and CSS, how to program in JavaScript and PHP, how to configure Apache and MySQL, how to design and query databases with SQL, how to use Ajax with both XML and JSON, and how to build mashups. The course explores issues of security, scalability, and cross-browser support and also discusses enterprise-level deployments of websites, including third-party hosting, virtualization, colocation in data centers, firewalling, and load-balancing.")
        self.assertEqual(len(result['entries']), 4)
        
    def test_ivi_compilation(self):
        dl = FakeYDL()
        ie = IviCompilationIE(dl)
        result = ie.extract('http://www.ivi.ru/watch/dezhurnyi_angel')
        self.assertIsPlaylist(result)
        self.assertEqual(result['id'], 'dezhurnyi_angel')
        self.assertEqual(result['title'], 'Дежурный ангел (2010 - 2012)')
        self.assertTrue(len(result['entries']) >= 36)
        
    def test_ivi_compilation_season(self):
        dl = FakeYDL()
        ie = IviCompilationIE(dl)
        result = ie.extract('http://www.ivi.ru/watch/dezhurnyi_angel/season2')
        self.assertIsPlaylist(result)
        self.assertEqual(result['id'], 'dezhurnyi_angel/season2')
        self.assertEqual(result['title'], 'Дежурный ангел (2010 - 2012) 2 сезон')
        self.assertTrue(len(result['entries']) >= 20)
        
    def test_imdb_list(self):
        dl = FakeYDL()
        ie = ImdbListIE(dl)
        result = ie.extract('http://www.imdb.com/list/JFs9NWw6XI0')
        self.assertIsPlaylist(result)
        self.assertEqual(result['id'], 'JFs9NWw6XI0')
        self.assertEqual(result['title'], 'March 23, 2012 Releases')
        self.assertEqual(len(result['entries']), 7)

    def test_khanacademy_topic(self):
        dl = FakeYDL()
        ie = KhanAcademyIE(dl)
        result = ie.extract('https://www.khanacademy.org/math/applied-math/cryptography')
        self.assertIsPlaylist(result)
        self.assertEqual(result['id'], 'cryptography')
        self.assertEqual(result['title'], 'Journey into cryptography')
        self.assertEqual(result['description'], 'How have humans protected their secret messages through history? What has changed today?')
        self.assertTrue(len(result['entries']) >= 3)

    def test_EveryonesMixtape(self):
        dl = FakeYDL()
        ie = EveryonesMixtapeIE(dl)
        result = ie.extract('http://everyonesmixtape.com/#/mix/m7m0jJAbMQi')
        self.assertIsPlaylist(result)
        self.assertEqual(result['id'], 'm7m0jJAbMQi')
        self.assertEqual(result['title'], 'Driving')
        self.assertEqual(len(result['entries']), 24)
        
    def test_rutube_channel(self):
        dl = FakeYDL()
        ie = RutubeChannelIE(dl)
        result = ie.extract('http://rutube.ru/tags/video/1409')
        self.assertIsPlaylist(result)
        self.assertEqual(result['id'], '1409')
        self.assertTrue(len(result['entries']) >= 34)

    def test_multiple_brightcove_videos(self):
        # https://github.com/rg3/youtube-dl/issues/2283
        dl = FakeYDL()
        ie = GenericIE(dl)
        result = ie.extract('http://www.newyorker.com/online/blogs/newsdesk/2014/01/always-never-nuclear-command-and-control.html')
        self.assertIsPlaylist(result)
        self.assertEqual(result['id'], 'always-never-nuclear-command-and-control')
        self.assertEqual(result['title'], 'Always/Never: A Little-Seen Movie About Nuclear Command and Control : The New Yorker')
        self.assertEqual(len(result['entries']), 3)

    def test_GoogleSearch(self):
        dl = FakeYDL()
        ie = GoogleSearchIE(dl)
        result = ie.extract('gvsearch15:python language')
        self.assertIsPlaylist(result)
        self.assertEqual(result['id'], 'python language')
        self.assertEqual(result['title'], 'python language')
        self.assertEqual(len(result['entries']), 15)

    def test_generic_rss_feed(self):
        dl = FakeYDL()
        ie = GenericIE(dl)
        result = ie.extract('http://phihag.de/2014/youtube-dl/rss.xml')
        self.assertIsPlaylist(result)
        self.assertEqual(result['id'], 'http://phihag.de/2014/youtube-dl/rss.xml')
        self.assertEqual(result['title'], 'Zero Punctuation')
        self.assertTrue(len(result['entries']) > 10)

    def test_ted_playlist(self):
        dl = FakeYDL()
        ie = TEDIE(dl)
        result = ie.extract('http://www.ted.com/playlists/who_are_the_hackers')
        self.assertIsPlaylist(result)
        self.assertEqual(result['id'], '10')
        self.assertEqual(result['title'], 'Who are the hackers?')
        self.assertTrue(len(result['entries']) >= 6)

    def test_toypics_user(self):
        dl = FakeYDL()
        ie = ToypicsUserIE(dl)
        result = ie.extract('http://videos.toypics.net/Mikey')
        self.assertIsPlaylist(result)
        self.assertEqual(result['id'], 'Mikey')
        self.assertTrue(len(result['entries']) >= 17)

if __name__ == '__main__':
    unittest.main()
