# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class TMZIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?tmz\.com/videos/(?P<id>[^/]+)/?'
    _TEST = {
        'url': 'http://www.tmz.com/videos/0_okj015ty/',
        'md5': '791204e3bf790b1426cb2db0706184c0',
        'info_dict': {
            'id': '0_okj015ty',
            'url': 'http://tmz.vo.llnwd.net/o28/2014-03/13/0_okj015ty_0_rt8ro3si_2.mp4',
            'ext': 'mp4',
            'title': 'Kim Kardashian\'s Boobs Unlock a Mystery!',
            'description': 'Did Kim Kardasain try to one-up Khloe by one-upping Kylie???  Or is she just showing off her amazing boobs?',
            'thumbnail': r're:http://cdnbakmi\.kaltura\.com/.*thumbnail.*',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        return {
            'id': video_id,
            'url': self._html_search_meta('VideoURL', webpage, fatal=True),
            'title': self._og_search_title(webpage),
            'description': self._og_search_description(webpage),
            'thumbnail': self._html_search_meta('ThumbURL', webpage),
        }


class TMZArticleIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?tmz\.com/\d{4}/\d{2}/\d{2}/(?P<id>[^/]+)/?'
    _TEST = {
        'url': 'http://www.tmz.com/2015/04/19/bobby-brown-bobbi-kristina-awake-video-concert',
        'md5': 'e482a414a38db73087450e3a6ce69d00',
        'info_dict': {
            'id': '0_6snoelag',
            'ext': 'mp4',
            'title': 'Bobby Brown Tells Crowd ... Bobbi Kristina is Awake',
            'description': 'Bobby Brown stunned his audience during a concert Saturday night, when he told the crowd, "Bobbi is awake.  She\'s watching me."',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)
        embedded_video_info_str = self._html_search_regex(
            r'tmzVideoEmbedV2\("([^)]+)"\);', webpage, 'embedded video info')

        embedded_video_info = self._parse_json(
            embedded_video_info_str, video_id,
            transform_source=lambda s: s.replace('\\', ''))

        return self.url_result(
            'http://www.tmz.com/videos/%s/' % embedded_video_info['id'])
