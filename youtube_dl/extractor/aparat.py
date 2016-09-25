# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import ExtractorError, HEADRequest


class AparatIE(InfoExtractor):
    _VALID_URL = r'^https?://(?:www\.)?aparat\.com/(?:v/|video/video/embed/videohash/)(?P<id>[a-zA-Z0-9]+)'

    _TEST = {
        'url': 'http://www.aparat.com/v/wP8On',
        'md5': '131aca2e14fe7c4dcb3c4877ba300c89',
        'info_dict': {
            'id': 'wP8On',
            'ext': 'mp4',
            'title': 'تیم گلکسی 11 - زومیت',
            'age_limit': 0,
        },
        # 'skip': 'Extremely unreliable',
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        # Note: There is an easier-to-parse configuration at
        # http://www.aparat.com/video/video/config/videohash/%video_id
        # but the URL in there does not work
        embed_url = 'http://www.aparat.com/video/video/embed/vt/frame/showvideo/yes/videohash/' + video_id
        webpage = self._download_webpage(embed_url, video_id)

        patterns = [
            r'fileList\s*=\s*JSON\.parse\(\'([^\']+)\'\)',
            r'fileListPseudo\s*=\s*JSON\.parse\(\'([^\']+)\'\)'
        ]
        file_list = []
        for p in patterns:
            res = self._parse_json(
                self._search_regex(p, webpage, 'file list', default='[]'),
                video_id
            )
            if res:
                file_list.extend(res[0])

        prefs = {
            'unknown': 0,
            '270p': 1,
            '360p': 2,
            '720p': 3,
            '1080p': 4
        }
        formats = []
        for i, item in enumerate(file_list):
            # check for video availability
            video_url = item['file']
            req = HEADRequest(video_url)
            res = self._request_webpage(
                req,
                video_id,
                note='Testing video URL %d' % (i + 1),
                errnote=False
            )
            if not res:
                continue

            video = {}
            video['url'] = item['file']
            video['format'] = item['type']
            video['ext'] = 'mp4'
            video_pref = item.get('label', 'unknown')
            video['preference'] = prefs.get(video_pref, -1)

            formats.append(video)

        if not formats:
            raise ExtractorError('No working video URLs found')

        self._sort_formats(formats)
        title = self._search_regex(
            r'\s+title:\s*"([^"]+)"',
            webpage,
            'title'
        )
        thumbnail = self._search_regex(
            r'image:\s*"([^"]+)"',
            webpage,
            'thumbnail',
            fatal=False
        )

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'thumbnail': thumbnail,
            'age_limit': self._family_friendly_search(webpage),
        }
