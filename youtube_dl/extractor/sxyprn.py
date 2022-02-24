from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    parse_duration,
    urljoin,
)


class SxyPrnIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?sxyprn\.com/post/(?P<id>[^/?#&.]+)'
    _TESTS = [{
        'url': 'https://sxyprn.com/post/57ffcb2e1179b.html',
        'md5': '6f8682b6464033d87acaa7a8ff0c092e',
        'info_dict': {
            'id': '57ffcb2e1179b',
            'ext': 'mp4',
            'title': 'md5:c9f43630bd968267672651ba905a7d35',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 165,
            'age_limit': 18,
            'tags': ['porn', 'gratis porno', 'anal', 'free porn videos', 'videos', 'movies'],
            'uploader': 'PornHot',
            'uploader_id': 'PornHot',
            'uploader_url': 'https://sxyprn.com/blog/porn-hot/0.html',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://sxyprn.com/post/57ffcb2e1179b.html',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        parts = self._parse_json(
            self._search_regex(
                r'data-vnfo=(["\'])(?P<data>{.+?})\1', webpage, 'data info',
                group='data'),
            video_id)[video_id].split('/')

        num = 0
        for c in parts[6] + parts[7]:
            if c.isnumeric():
                num += int(c)
        parts[5] = compat_str(int(parts[5]) - num)
        parts[1] += '8'
        video_url = urljoin(url, '/'.join(parts))

        title = (self._search_regex(
            r'<[^>]+\bclass=["\']PostEditTA[^>]+>([^<]+)', webpage, 'title',
            default=None) or self._og_search_description(webpage)).strip()
        thumbnail = self._og_search_thumbnail(webpage)
        duration = parse_duration(self._search_regex(
            r'duration\s*:\s*<[^>]+>([\d:]+)', webpage, 'duration',
            default=None))
        tags = self._search_regex(r'<meta name="keywords".+content="(?P<tags>.+)"', webpage, 'tags', group='tags').split(', ')
        uploader = self._search_regex(r'<div class=\'pes_author_div pes_edit_div transition\'.+?>.+?<span class=\'a_name\'>(?P<uploader>.+?)<', webpage, 'uploader', group='uploader')
        uploader_url = urljoin(url, self._search_regex(r'<div class=\'pes_author_div pes_edit_div transition\'.+?><a href=\'(?P<uploader_url>.+?)\'.+?<span class=\'a_name\'>(?P<uploader>.+?)<', webpage, 'uploader_url', group='uploader_url'))

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'thumbnail': thumbnail,
            'duration': duration,
            'age_limit': 18,
            'ext': 'mp4',
            'tags': tags,
            'uploader': uploader,
            'uploader_id': uploader,
            'uploader_url': uploader_url,
        }
