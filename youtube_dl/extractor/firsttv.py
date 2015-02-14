# encoding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import int_or_none


class FirstTVIE(InfoExtractor):
    IE_NAME = '1tv'
    IE_DESC = 'Первый канал'
    _VALID_URL = r'http://(?:www\.)?1tv\.ru/(?:[^/]+/)+(?P<id>.+)'

    _TESTS = [{
        'url': 'http://www.1tv.ru/videoarchive/73390',
        'md5': '777f525feeec4806130f4f764bc18a4f',
        'info_dict': {
            'id': '73390',
            'ext': 'mp4',
            'title': 'Олимпийские канатные дороги',
            'description': 'md5:d41d8cd98f00b204e9800998ecf8427e',
            'thumbnail': 're:^https?://.*\.(?:jpg|JPG)$',
            'duration': 149,
            'like_count': int,
            'dislike_count': int,
        },
        'skip': 'Only works from Russia',
    }, {
        'url': 'http://www.1tv.ru/prj/inprivate/vypusk/35930',
        'md5': 'a1b6b60d530ebcf8daacf4565762bbaf',
        'info_dict': {
            'id': '35930',
            'ext': 'mp4',
            'title': 'Наедине со всеми. Людмила Сенчина',
            'description': 'md5:89553aed1d641416001fe8d450f06cb9',
            'thumbnail': 're:^https?://.*\.(?:jpg|JPG)$',
            'duration': 2694,
        },
        'skip': 'Only works from Russia',
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id, 'Downloading page')

        video_url = self._html_search_regex(
            r'''(?s)(?:jwplayer\('flashvideoportal_1'\)\.setup\({|var\s+playlistObj\s*=).*?'file'\s*:\s*'([^']+)'.*?}\);''',
            webpage, 'video URL')

        title = self._html_search_regex(
            [r'<div class="tv_translation">\s*<h1><a href="[^"]+">([^<]*)</a>',
             r"'title'\s*:\s*'([^']+)'"], webpage, 'title')
        description = self._html_search_regex(
            r'<div class="descr">\s*<div>&nbsp;</div>\s*<p>([^<]*)</p></div>',
            webpage, 'description', default=None) or self._html_search_meta(
                'description', webpage, 'description')

        thumbnail = self._og_search_thumbnail(webpage)
        duration = self._og_search_property(
            'video:duration', webpage,
            'video duration', fatal=False)

        like_count = self._html_search_regex(
            r'title="Понравилось".*?/></label> \[(\d+)\]',
            webpage, 'like count', default=None)
        dislike_count = self._html_search_regex(
            r'title="Не понравилось".*?/></label> \[(\d+)\]',
            webpage, 'dislike count', default=None)

        return {
            'id': video_id,
            'url': video_url,
            'thumbnail': thumbnail,
            'title': title,
            'description': description,
            'duration': int_or_none(duration),
            'like_count': int_or_none(like_count),
            'dislike_count': int_or_none(dislike_count),
        }
