from __future__ import unicode_literals

import re

from .common import InfoExtractor


class SpankBangIE(InfoExtractor):
    _VALID_URL = r'https?://(?:(?:www|[a-z]{2})\.)?spankbang\.com/(?P<id>[\da-z]+)/video'
    _TESTS = [{
        'url': 'http://spankbang.com/3vvn/video/fantasy+solo',
        'md5': '1cc433e1d6aa14bc376535b8679302f7',
        'info_dict': {
            'id': '3vvn',
            'ext': 'mp4',
            'title': 'fantasy solo',
            'description': 'Watch fantasy solo free HD porn video - 05 minutes - dillion harper masturbates on a bed free adult movies.',
            'thumbnail': r're:^https?://.*\.jpg$',
            'uploader': 'silly2587',
            'age_limit': 18,
        }
    }, {
        # 480p only
        'url': 'http://spankbang.com/1vt0/video/solvane+gangbang',
        'only_matching': True,
    }, {
        # no uploader
        'url': 'http://spankbang.com/lklg/video/sex+with+anyone+wedding+edition+2',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        stream_key = self._html_search_regex(
            r'''var\s+stream_key\s*=\s*['"](.+?)['"]''',
            webpage, 'stream key')

        formats = [{
            'url': 'http://spankbang.com/_%s/%s/title/%sp__mp4' % (video_id, stream_key, height),
            'ext': 'mp4',
            'format_id': '%sp' % height,
            'height': int(height),
        } for height in re.findall(r'<(?:span|li|p)[^>]+[qb]_(\d+)p', webpage)]
        self._check_formats(formats, video_id)
        self._sort_formats(formats)

        title = self._html_search_regex(
            r'(?s)<h1[^>]*>(.+?)</h1>', webpage, 'title')
        description = self._og_search_description(webpage)
        thumbnail = self._og_search_thumbnail(webpage)
        uploader = self._search_regex(
            r'class="user"[^>]*><img[^>]+>([^<]+)',
            webpage, 'uploader', default=None)

        age_limit = self._rta_search(webpage)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'formats': formats,
            'age_limit': age_limit,
        }
