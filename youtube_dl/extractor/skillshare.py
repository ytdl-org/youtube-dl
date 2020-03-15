# coding: utf-8
from __future__ import unicode_literals
from .common import InfoExtractor
from .brightcove import BrightcoveNewIE


class SkillshareClassIE(InfoExtractor):
    IE_NAME = 'skillshare:class'
    _VALID_URL = r'https?://(?:www\.)?skillshare\.com/classes/[^/]+/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://www.skillshare.com/classes/SEO-Today-Strategies-to-Earn-Trust-Rank-High-and-Stand-Out/423483018',
        'only_matching': True,
    }

    def _real_extract(self, url):
        class_id = self._match_id(url)
        class_json_data = self._parse_json(self._search_regex(r'(?P<json_line>{"userData":{.+});\n', self._download_webpage(url, class_id), 'class_json_data'), class_id)
        account_id = str(class_json_data['pageData']['videoPlayerData']['brightcoveAccountId'])
        lessons = class_json_data['pageData']['videoPlayerData']['units'][0]['sessions']
        entries = []
        for lesson in lessons:
            lesson_id = str(lesson['id'])
            lesson_info_api_response = self._download_json("https://www.skillshare.com/sessions/{}/video".format(lesson_id), lesson_id)
            if 'video_hashed_id' not in lesson_info_api_response:
                break
            video_hashed_id = lesson_info_api_response['video_hashed_id'][3:]
            entry = {
                '_type': 'url_transparent',
                'id': video_hashed_id,
                'title': lesson['title'],
                'ie_key': BrightcoveNewIE.ie_key(),
                'url': 'https://players.brightcove.net/{}/default_default/index.html?videoId={}'.format(account_id, video_hashed_id),
            }
            entries.append(entry)
        return self.playlist_result(entries, class_id, class_json_data['pageData']['headerData']['title'], class_json_data.get("pageData").get('sectionData').get('description'))
