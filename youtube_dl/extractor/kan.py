# coding: utf-8
from __future__ import unicode_literals
from ..compat import compat_str
import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    parse_duration,
    try_get,
    unified_strdate)


def get_thumbnail(data):
    for media in data.get('media_group', []):
        if media.get('type') == 'image':
            for item in media.get('media_item', []):
                thumbnail = item.get('src')
                if thumbnail:
                    return thumbnail


class KanBaseIE(InfoExtractor):
    def download_webpage(self, url, video_id):
        return self._download_webpage(
            url,
            video_id)

    def extract_item(self, video_id, webpage):
        data = self._parse_json(
            self._search_regex(
                r'<script[^>]+id="kan_app_search_data"[^>]*>([^<]+)</script>',
                webpage,
                'data'),
            video_id)
        title = data.get('title') or self._og_search_title(webpage)
        m3u8_url = try_get(data, lambda x: x['content']['src'], compat_str)
        formats = self._extract_m3u8_formats(m3u8_url, video_id, ext='mp4')
        if not formats:
            raise ExtractorError('Unable to extract video formats')
        description = data.get('summary') or \
            self._og_search_description(webpage, fatal=False)
        creator = try_get(data, lambda x: x['author']['name'], compat_str) or \
            self._og_search_property('site_name', webpage, fatal=False)
        thumbnail = get_thumbnail(data)

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'formats': formats,
            'description': description,
            'creator': creator,
            'release_date': unified_strdate(data.get('published')),
            'duration': parse_duration(
                try_get(data, lambda x: x['extensions']['duration']))
        }


class KanEpisodeIE(KanBaseIE):
    _VALID_URL = r'https?://(?:www\.)?kan\.org\.il/[iI]tem/\?item[iI]d=(?P<id>[0-9]+)'
    _TEST = {
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
            'duration': 2393,
        },
        'params': {
            'skip_download': True
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        return self.extract_item(video_id, self.download_webpage(url, video_id))


class KanPlaylistIE(KanBaseIE):
    _VALID_URL = r'https?://(?:www\.)?kan\.org\.il/program/\?cat[iI]d=(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://www.kan.org.il/program/?catId=1636',
        'playlist_mincount': 9,
        'info_dict': {
            'id': '1636',
            'title': 'מנאייכ - פרקים מלאים לצפייה ישירה | כאן',
            'description': 'md5:9dfbd501189d08674d20762464c5301b',
        },
    }

    def _real_extract(self, url):
        list_id = self._match_id(url)
        webpage = self.download_webpage(url, list_id)
        video_ids = re.findall(r'onclick="playVideo\(.*,\'([0-9]+)\'\)', webpage)
        entries = []
        for video_id in video_ids:
            video_url = 'https://www.kan.org.il/Item/?itemId=%s' % video_id
            entries.append(self.extract_item(
                video_id,
                self.download_webpage(video_url, video_id)))
        if not entries:
            raise ExtractorError('Unable to extract playlist entries')

        return {
            '_type': 'playlist',
            'id': list_id,
            'entries': entries,
            'title': self._og_search_title(webpage, fatal=False),
            'description': self._og_search_description(webpage),
        }
