# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class TMZIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?tmz\.com/videos/(?P<id>[^/?#]+)'
    _TESTS = [{
        'url': 'http://www.tmz.com/videos/0_okj015ty/',
        'md5': '4d22a51ef205b6c06395d8394f72d560',
        'info_dict': {
            'id': '0_okj015ty',
            'ext': 'mp4',
            'title': 'Kim Kardashian\'s Boobs Unlock a Mystery!',
            'description': 'Did Kim Kardasain try to one-up Khloe by one-upping Kylie???  Or is she just showing off her amazing boobs?',
            'timestamp': 1394747163,
            'uploader_id': 'batchUser',
            'upload_date': '20140313',
        }
    }, {
        'url': 'http://www.tmz.com/videos/0-cegprt2p/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url).replace('-', '_')
        return self.url_result('kaltura:591531:%s' % video_id, 'Kaltura', video_id)


class TMZArticleIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?tmz\.com/\d{4}/\d{2}/\d{2}/(?P<id>[^/]+)/?'
    _TEST = {
        'url': 'http://www.tmz.com/2015/04/19/bobby-brown-bobbi-kristina-awake-video-concert',
        'md5': '3316ff838ae5bb7f642537825e1e90d2',
        'info_dict': {
            'id': '0_6snoelag',
            'ext': 'mov',
            'title': 'Bobby Brown Tells Crowd ... Bobbi Kristina is Awake',
            'description': 'Bobby Brown stunned his audience during a concert Saturday night, when he told the crowd, "Bobbi is awake.  She\'s watching me."',
            'timestamp': 1429467813,
            'upload_date': '20150419',
            'uploader_id': 'batchUser',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)
        embedded_video_info = self._parse_json(self._html_search_regex(
            r'tmzVideoEmbed\(({.+?})\);', webpage, 'embedded video info'),
            video_id)

        return self.url_result(
            'http://www.tmz.com/videos/%s/' % embedded_video_info['id'])
