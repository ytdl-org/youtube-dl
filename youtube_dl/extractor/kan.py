# coding: utf-8
from __future__ import unicode_literals
import re

from .common import InfoExtractor
from ..utils import unified_strdate, parse_duration


def get_thumbnail(data):
    for media in data.get('media_group', []):
        if media.get('type') == 'image':
            for item in media.get('media_item'):
                thumbnail = item.get('src')
                if thumbnail:
                    return thumbnail


class KanIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?kan\.org\.il/(?:[iI]tem/\?item[iI]d|program/\?cat[iI]d)=(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'https://www.kan.org.il/Item/?itemId=74658',
        'md5': 'c28763bdb61c1bb7823528dd024e6129',
        'info_dict': {
            'id': '74658',
            'ext': 'mp4',
            'title': 'העד - פרק 2',
            'thumbnail': r're:^https://.*36805_A\.jpeg$',
            'description': 'הגופות ממשיכות להיערם, אך איזי עדיין מפקפק בחשדות נגד ברק',
            'creator': 'מערכת כאן',
            'release_date': '20200803',
            'duration': 2393}
    }, {
        'url': 'https://www.kan.org.il/program/?catId=1636',
        'playlist_mincount': 9,
        'info_dict': {
            'id': '1636',
            'title': 'מנאייכ - פרקים מלאים לצפייה ישירה | כאן',
            'description': 'md5:9dfbd501189d08674d20762464c5301b'
        }
    }]
    _GEO_COUNTRIES = ['IL']

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(
            url,
            video_id,
            headers=self.geo_verification_headers())
        if 'itemid' in url.lower():
            return self._extract_item(video_id, webpage)
        elif 'catid' in url.lower():
            return self._extract_list(video_id, webpage)
        return {}

    def _extract_list(self, list_id, webpage):
        ids = re.findall(r'onclick="playVideo\(.*,\'([0-9]+)\'\)', webpage)
        title = self._og_search_title(webpage)
        description = self._og_search_description(webpage)
        entries = []
        for video_id in ids:
            url = 'https://www.kan.org.il/Item/?itemId=%s' % video_id
            webpage = self._download_webpage(
                url,
                video_id,
                headers=self.geo_verification_headers())
            entries.append(self._extract_item(video_id, webpage))
        return {
            '_type': 'playlist',
            'id': list_id,
            'entries': entries,
            'title': title,
            'description': description
        }

    def _extract_item(self, video_id, webpage):
        data = self._parse_json(
            self._search_regex(
                r'<script id="kan_app_search_data" type="application/json">([^<]+)</script>',
                webpage, 'data'),
            video_id)
        title = data.get('title') or \
            self._og_search_title(webpage) or \
            self._html_search_regex(r'<title>([^<]+)</title>', webpage, 'title')
        description = data.get('summary') or \
            self._og_search_description(webpage, fatal=False)
        creator = data.get('author', {}).get('name') or \
            self._og_search_property('site_name', webpage, fatal=False)
        thumbnail = get_thumbnail(data)
        m3u8_url = data.get('content', {}).get('src')
        formats = self._extract_m3u8_formats(m3u8_url, video_id, ext='mp4')
        return {
            '_type': 'video',
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'formats': formats,
            'description': description,
            'creator': creator,
            'release_date': unified_strdate(data.get('published')),
            'duration': parse_duration(data.get('extensions', {}).get('duration'))
        }
