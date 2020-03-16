# coding: utf-8
from __future__ import unicode_literals
from .common import InfoExtractor
from .brightcove import BrightcoveNewIE
from ..utils import (
    try_get,
    compat_str
)


class SkillshareClassIE(InfoExtractor):
    IE_NAME = 'skillshare:class'
    _VALID_URL = r'https?://(?:www\.)?skillshare\.com/classes/[^/]+/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://www.skillshare.com/classes/SEO-Today-Strategies-to-Earn-Trust-Rank-High-and-Stand-Out/423483018',
        'only_matching': True,
    }

    def _real_extract(self, url):
        class_id = self._match_id(url)
        class_json_data = self._parse_json(self._search_regex(
            r'(?P<json_line>{.+pageData.+});\n',
            self._download_webpage(url, class_id), 'class_json_data'), class_id)
        account_id = class_json_data['pageData']['videoPlayerData']['brightcoveAccountId']
        lessons = class_json_data['pageData']['videoPlayerData']['units'][0]['sessions']
        entries = []
        for lesson in lessons:
            lesson_id = lesson.get('id')
            lesson_info_api_response = self._download_json(
                "https://www.skillshare.com/sessions/%s/video" % lesson_id,
                lesson_id)
            if 'video_hashed_id' not in lesson_info_api_response:
                break
            video_hashed_id = self._search_regex(
                r'(\d+)', lesson_info_api_response.get('video_hashed_id'),
                'video_hashed_id')
            entry = {
                # the brightcove extractor extracts the title and id
                '_type': 'url_transparent',
                'ie_key': BrightcoveNewIE.ie_key(),
                'url': 'https://players.brightcove.net/%s/default_default/index.html?videoId=%s' % (account_id, video_hashed_id),
            }
            entries.append(entry)
        return self.playlist_result(
            entries, class_id, try_get(
                class_json_data, lambda x: x['pageData']['headerData']['title'],
                compat_str),
            try_get(
                class_json_data, lambda x: x['pageData']['sectionData']['description'],
                compat_str))
