# coding: utf-8
from __future__ import unicode_literals
import json
from .common import InfoExtractor


class SkillshareClassIE(InfoExtractor):
    IE_NAME = 'skillshare:class'
    _VALID_URL = r'https?://(?:www\.)?skillshare\.com/classes/[^/]+/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://www.skillshare.com/classes/SEO-Today-Strategies-to-Earn-Trust-Rank-High-and-Stand-Out/423483018',
        'only_matching': True,
        'info_dict': {
            'id': '5463396146001',
            'ext': 'mp4',
            'title': 'Introduction',
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
    }

    def _real_extract(self, url):
        search_term = r'(?P<json_line>{"userData":{.+});\n'
        lesson_info_api_url_format = "https://www.skillshare.com/sessions/{}/video"
        video_api_url_format = "https://edge.api.brightcove.com/playback/v1/accounts/{}/videos/{}"
        headers = {"Accept": "application/json;pk=BCpkADawqM2OOcM6njnM7hf9EaK6lIFlqiXB0iWjqGWU    QjU7R8965xUvIQNqdQbnDTLz0IAO7E6Ir2rIbXJtFdzrGtitoee0n1XXRliD-RH9A-svuvNW    9qgo3Bh34HEZjXjG4Nml4iyz3KqF"}
        class_id = self._match_id(url)
        class_page = self._download_webpage(url, class_id)
        class_json_data = json.loads(self._search_regex(search_term, class_page, 'class_json_data'))
        account_id = str(class_json_data.get('pageData').get('videoPlayerData').get('brightcoveAccountId'))
        class_title = class_json_data.get('pageData').get('headerData').get('title')
        lessons = class_json_data.get('pageData').get('videoPlayerData').get('units')[0].get('sessions')
        videos = []
        for lesson in lessons:
            lesson_id = str(lesson.get('id'))
            lesson_info_api_url = lesson_info_api_url_format.format(lesson_id)
            lesson_info_api_response = self._download_json(lesson_info_api_url, lesson_id)
            print(lesson_info_api_response)
            if 'video_hashed_id' not in lesson_info_api_response:
                break
            video_hashed_id = lesson_info_api_response.get('video_hashed_id')[3:]
            video_api_url = video_api_url_format.format(account_id, video_hashed_id)
            video_api_response = self._download_json(video_api_url, video_hashed_id, headers=headers)
            lesson_title = lesson.get('title')
            lesson_url = video_api_response.get('sources')[-1].get('src')
            video = {
                'id': video_hashed_id,
                'title': lesson_title,
                'url': lesson_url,
                'ext': 'mp4',
            }
            videos.append(video)
        return {
            'id': class_id,
            'title': class_title,
            '_type': 'playlist',
            'entries': videos
        }
