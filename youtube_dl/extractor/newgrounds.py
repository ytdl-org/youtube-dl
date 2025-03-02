from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    extract_attributes,
    parse_duration,
    parse_filesize,
    unified_timestamp,
)


class NewgroundsIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?newgrounds\.com/(?:audio/listen|portal/view)/(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'https://www.newgrounds.com/audio/listen/549479',
        'md5': 'fe6033d297591288fa1c1f780386f07a',
        'info_dict': {
            'id': '549479',
            'ext': 'mp3',
            'title': 'B7 - BusMode',
            'uploader': 'Burn7',
            'timestamp': 1378878540,
            'upload_date': '20130911',
            'duration': 143,
        },
    }, {
        'url': 'https://www.newgrounds.com/portal/view/850292',
        'md5': 'bb7cacf45e1b4d648e2dac2d79284d67',
        'info_dict': {
            'id': '850292',
            'ext': 'mp4',
            'title': 'Timeless (2021)',
            'uploader': 'Kevuhn',
            'timestamp': 1657896960,
            'upload_date': '20220715',
        },
    }, {
        # source format unavailable, additional mp4 formats
        'url': 'http://www.newgrounds.com/portal/view/689400',
        'info_dict': {
            'id': '689400',
            'ext': 'mp4',
            'title': 'ZTV News Episode 8',
            'uploader': 'ZONE-SAMA',
            'timestamp': 1487965140,
            'upload_date': '20170224',
        },
        'params': {
            'skip_download': True,
        },
    }]

    def _real_extract(self, url):
        media_id = self._match_id(url)

        webpage = self._download_webpage(url, media_id)

        paths = url.split('/')
        if paths[-3] == 'audio':
            isAudio = True
        else:
            isAudio = False

        if isAudio:
            media_url = self._parse_json(self._search_regex(
                r'"url"\s*:\s*("[^"]+"),', webpage, ''), media_id)

            uploader = self._html_search_regex(
                (r'(?s)<h4[^>]*>(.+?)</h4>.*?<em>\s*Author\s*</em>',
                 r'(?:Author|Writer)\s*<a[^>]+>([^<]+)'), webpage, 'uploader',
                fatal=False)

            formats = [{
                'url': media_url,
                'format_id': 'source',
                'quality': 1,
            }]

        else:
            media_url = 'https://www.newgrounds.com/portal/video/' + media_id
            media = self._download_json(media_url, media_id, headers={'X-Requested-With': 'XMLHttpRequest'})

            uploader = media['author']

            sources = media['sources']

            formats = []
            for source in sources:
                for i in range(len(sources[source])):
                    formats.append({
                        'url': sources[source][i]['src'],
                        'format_id': source,
                        'height': int(source[:-2])  # 1080p -> 1080
                    })

        title = self._html_search_regex(
            r'<title>([^>]+)</title>', webpage, 'title')
        timestamp = unified_timestamp(self._html_search_regex(
            (r'<dt>\s*Uploaded\s*</dt>\s*<dd>([^<]+</dd>\s*<dd>[^<]+)',
             r'<dt>\s*Uploaded\s*</dt>\s*<dd>([^<]+)'), webpage, 'timestamp',
            default=None))
        duration = parse_duration(self._search_regex(
            r'(?s)<dd>\s*Song\s*</dd>\s*<dd>.+?</dd>\s*<dd>([^<]+)', webpage,
            'duration', default=None))
        filesize_approx = parse_filesize(self._html_search_regex(
            r'(?s)<dd>\s*Song\s*</dd>\s*<dd>(.+?)</dd>', webpage, 'filesize',
            default=None))
        if len(formats) == 1:
            formats[0]['filesize_approx'] = filesize_approx

        if '<dd>Song' in webpage:
            formats[0]['vcodec'] = 'none'

        self._check_formats(formats, media_id)
        self._sort_formats(formats)

        return {
            'id': media_id,
            'title': title,
            'uploader': uploader,
            'timestamp': timestamp,
            'duration': duration,
            'formats': formats,
        }


class NewgroundsPlaylistIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?newgrounds\.com/(?:collection|[^/]+/search/[^/]+)/(?P<id>[^/?#&]+)'
    _TESTS = [{
        'url': 'https://www.newgrounds.com/collection/cats',
        'info_dict': {
            'id': 'cats',
            'title': 'Cats',
        },
        'playlist_mincount': 46,
    }, {
        'url': 'http://www.newgrounds.com/portal/search/author/ZONE-SAMA',
        'info_dict': {
            'id': 'ZONE-SAMA',
            'title': 'Portal Search: ZONE-SAMA',
        },
        'playlist_mincount': 47,
    }, {
        'url': 'http://www.newgrounds.com/audio/search/title/cats',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)

        webpage = self._download_webpage(url, playlist_id)

        title = self._search_regex(
            r'<title>([^>]+)</title>', webpage, 'title', default=None)

        # cut left menu
        webpage = self._search_regex(
            r'(?s)<div[^>]+\bclass=["\']column wide(.+)',
            webpage, 'wide column', default=webpage)

        entries = []
        for a, path, media_id in re.findall(
                r'(<a[^>]+\bhref=["\']/?((?:portal/view|audio/listen)/(\d+))[^>]+>)',
                webpage):
            a_class = extract_attributes(a).get('class')
            if a_class not in ('item-portalsubmission', 'item-audiosubmission'):
                continue
            entries.append(
                self.url_result(
                    'https://www.newgrounds.com/%s' % path,
                    ie=NewgroundsIE.ie_key(), video_id=media_id))

        return self.playlist_result(entries, playlist_id, title)
