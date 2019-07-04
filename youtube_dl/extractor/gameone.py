# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    xpath_with_ns,
    parse_iso8601,
    float_or_none,
    int_or_none,
)

NAMESPACE_MAP = {
    'media': 'http://search.yahoo.com/mrss/',
}

# URL prefix to download the mp4 files directly instead of streaming via rtmp
# Credits go to XBox-Maniac
# http://board.jdownloader.org/showpost.php?p=185835&postcount=31
RAW_MP4_URL = 'http://cdn.riptide-mtvn.com/'


class GameOneIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?gameone\.de/tv/(?P<id>\d+)'
    _TESTS = [
        {
            'url': 'http://www.gameone.de/tv/288',
            'md5': '136656b7fb4c9cb4a8e2d500651c499b',
            'info_dict': {
                'id': '288',
                'ext': 'mp4',
                'title': 'Game One - Folge 288',
                'duration': 1238,
                'thumbnail': 'http://s3.gameone.de/gameone/assets/video_metas/teaser_images/000/643/636/big/640x360.jpg',
                'description': 'FIFA-Pressepokal 2014, Star Citizen, Kingdom Come: Deliverance, Project Cars, Schöner Trants Nerdquiz Folge 2 Runde 1',
                'age_limit': 16,
                'upload_date': '20140513',
                'timestamp': 1399980122,
            }
        },
        {
            'url': 'http://gameone.de/tv/220',
            'md5': '5227ca74c4ae6b5f74c0510a7c48839e',
            'info_dict': {
                'id': '220',
                'ext': 'mp4',
                'upload_date': '20120918',
                'description': 'Jet Set Radio HD, Tekken Tag Tournament 2, Source Filmmaker',
                'timestamp': 1347971451,
                'title': 'Game One - Folge 220',
                'duration': 896.62,
                'age_limit': 16,
            }
        }

    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)
        og_video = self._og_search_video_url(webpage, secure=False)
        description = self._html_search_meta('description', webpage)
        age_limit = int(
            self._search_regex(
                r'age=(\d+)',
                self._html_search_meta(
                    'age-de-meta-label',
                    webpage),
                'age_limit',
                '0'))
        mrss_url = self._search_regex(r'mrss=([^&]+)', og_video, 'mrss')

        mrss = self._download_xml(mrss_url, video_id, 'Downloading mrss')
        title = mrss.find('.//item/title').text
        thumbnail = mrss.find('.//item/image').get('url')
        timestamp = parse_iso8601(mrss.find('.//pubDate').text, delimiter=' ')
        content = mrss.find(xpath_with_ns('.//media:content', NAMESPACE_MAP))
        content_url = content.get('url')

        content = self._download_xml(
            content_url,
            video_id,
            'Downloading media:content')
        rendition_items = content.findall('.//rendition')
        duration = float_or_none(rendition_items[0].get('duration'))
        formats = [
            {
                'url': re.sub(r'.*/(r2)', RAW_MP4_URL + r'\1', r.find('./src').text),
                'width': int_or_none(r.get('width')),
                'height': int_or_none(r.get('height')),
                'tbr': int_or_none(r.get('bitrate')),
            }
            for r in rendition_items
        ]
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'duration': duration,
            'formats': formats,
            'description': description,
            'age_limit': age_limit,
            'timestamp': timestamp,
        }


class GameOnePlaylistIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?gameone\.de(?:/tv)?/?$'
    IE_NAME = 'gameone:playlist'
    _TEST = {
        'url': 'http://www.gameone.de/tv',
        'info_dict': {
            'title': 'GameOne',
        },
        'playlist_mincount': 294,
    }

    def _real_extract(self, url):
        webpage = self._download_webpage('http://www.gameone.de/tv', 'TV')
        max_id = max(map(int, re.findall(r'<a href="/tv/(\d+)"', webpage)))
        entries = [
            self.url_result('http://www.gameone.de/tv/%d' %
                            video_id, 'GameOne')
            for video_id in range(max_id, 0, -1)]

        return {
            '_type': 'playlist',
            'title': 'GameOne',
            'entries': entries,
        }
