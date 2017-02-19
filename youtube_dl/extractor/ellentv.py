# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from .kaltura import KalturaIE
from ..utils import NO_DEFAULT


class EllenTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?(?:ellentv|ellentube)\.com/videos/(?P<id>[a-z0-9_-]+)'
    _TESTS = [{
        'url': 'http://www.ellentv.com/videos/0-ipq1gsai/',
        'md5': '4294cf98bc165f218aaa0b89e0fd8042',
        'info_dict': {
            'id': '0_ipq1gsai',
            'ext': 'mov',
            'title': 'Fast Fingers of Fate',
            'description': 'md5:3539013ddcbfa64b2a6d1b38d910868a',
            'timestamp': 1428035648,
            'upload_date': '20150403',
            'uploader_id': 'batchUser',
        },
    }, {
        # not available via http://widgets.ellentube.com/
        'url': 'http://www.ellentv.com/videos/1-szkgu2m2/',
        'info_dict': {
            'id': '1_szkgu2m2',
            'ext': 'flv',
            'title': "Ellen's Amazingly Talented Audience",
            'description': 'md5:86ff1e376ff0d717d7171590e273f0a5',
            'timestamp': 1255140900,
            'upload_date': '20091010',
            'uploader_id': 'ellenkaltura@gmail.com',
        },
        'params': {
            'skip_download': True,
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        URLS = ('http://widgets.ellentube.com/videos/%s' % video_id, url)

        for num, url_ in enumerate(URLS, 1):
            webpage = self._download_webpage(
                url_, video_id, fatal=num == len(URLS))

            default = NO_DEFAULT if num == len(URLS) else None

            partner_id = self._search_regex(
                r"var\s+partnerId\s*=\s*'([^']+)", webpage, 'partner id',
                default=default)

            kaltura_id = self._search_regex(
                [r'id="kaltura_player_([^"]+)"',
                 r"_wb_entry_id\s*:\s*'([^']+)",
                 r'data-kaltura-entry-id="([^"]+)'],
                webpage, 'kaltura id', default=default)

            if partner_id and kaltura_id:
                break

        return self.url_result('kaltura:%s:%s' % (partner_id, kaltura_id), KalturaIE.ie_key())


class EllenTVClipsIE(InfoExtractor):
    IE_NAME = 'EllenTV:clips'
    _VALID_URL = r'https?://(?:www\.)?ellentv\.com/episodes/(?P<id>[a-z0-9_-]+)'
    _TEST = {
        'url': 'http://www.ellentv.com/episodes/meryl-streep-vanessa-hudgens/',
        'info_dict': {
            'id': 'meryl-streep-vanessa-hudgens',
            'title': 'Meryl Streep, Vanessa Hudgens',
        },
        'playlist_mincount': 5,
    }

    def _real_extract(self, url):
        playlist_id = self._match_id(url)

        webpage = self._download_webpage(url, playlist_id)
        playlist = self._extract_playlist(webpage, playlist_id)

        return {
            '_type': 'playlist',
            'id': playlist_id,
            'title': self._og_search_title(webpage),
            'entries': self._extract_entries(playlist)
        }

    def _extract_playlist(self, webpage, playlist_id):
        json_string = self._search_regex(r'playerView.addClips\(\[\{(.*?)\}\]\);', webpage, 'json')
        return self._parse_json('[{' + json_string + '}]', playlist_id)

    def _extract_entries(self, playlist):
        return [
            self.url_result(
                'kaltura:%s:%s' % (item['kaltura_partner_id'], item['kaltura_entry_id']),
                KalturaIE.ie_key(), video_id=item['kaltura_entry_id'])
            for item in playlist]
