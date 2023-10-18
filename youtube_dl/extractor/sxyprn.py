from __future__ import unicode_literals
import re

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    parse_duration,
    urljoin,
)


class SxyPrnIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?sxyprn\.com/post/(?P<id>[^/?#&.]+)'
    _TESTS = [{
        'url': 'https://sxyprn.com/post/6217e4ce4c36e.html',
        'md5': '6f8682b6464033d87acaa7a8ff0c092e',
        'info_dict': {
            'id': '6217e4ce4c36e',
            'ext': 'mp4',
            'title': 'md5:04e5427c36d2e9e229588059dac45a62',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 3813,
            'age_limit': 18,
            'tags': ['Nicole Love', 'Cindy Shine', 'Anal', 'DoublePenetration', 'GangBang', 'BigTits', 'BigAss', 'Blowjob'],
            'uploader': 'SmokeCrumb',
            'uploader_id': 'SmokeCrumb',
            'uploader_url': 'https://sxyprn.com/blog/608a6b540ee7b/0.html',
            'actors': [{'given_name': 'Nicole Love', 'url': 'https://sxyprn.com/Nicole-Love.html'}, {'given_name': 'Cindy Shine', 'url': 'https://sxyprn.com/Cindy-Shine.html'}],
            'view_count': int,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://sxyprn.com/post/6217e4ce4c36e.html',
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
        tags = self._search_regex(r'<meta name="keywords".+content="(?P<tags>.+)"', webpage, 'tags', group='tags', default='').split(', ')
        uploader = self._search_regex(r'<div class=\'pes_author_div pes_edit_div transition\'.+?>.+?<span class=\'a_name\'>(?P<uploader>.+?)<', webpage, 'uploader', group='uploader', default=None)
        uploader_url = urljoin(url, self._search_regex(r'<div class=\'pes_author_div pes_edit_div transition\'.+?><a href=\'(?P<uploader_url>.+?)\'.+?<span class=\'a_name\'>(?P<uploader>.+?)<', webpage, 'uploader_url', group='uploader_url'))
        actors_data = re.findall(r'<a href=\'(?P<actor_url>.+?)\' class=\'tdn htag_rel_a\'><div class=\'htag_rel\'><span>·</span><b>(?P<actor_name>.+?)</b>', webpage)
        actors = []
        if actors_data != []:
            for actor_tuple in actors_data:
                actors.append({
                    'given_name': actor_tuple[1],
                    'url': urljoin(url, actor_tuple[0])
                })
        views = int(self._search_regex(r'<div class=\'post_control_time\'>.+?</strong> (?P<views>.+) views</div>', webpage, 'views', group='views', default=0))

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'thumbnail': thumbnail,
            'duration': duration,
            'age_limit': 18,
            'ext': 'mp4',
            'tags': tags,
            'creator': uploader,
            'uploader': uploader,
            'uploader_id': uploader,
            'uploader_url': uploader_url,
            'actors': actors,
            'view_count': views,
        }
