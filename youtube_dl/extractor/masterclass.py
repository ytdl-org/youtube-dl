# coding: utf-8
from __future__ import unicode_literals
import re

from .brightcove import BrightcoveNewIE
from .common import InfoExtractor
from ..utils import (
    int_or_none,
    url_or_none,
    parse_duration,
    unified_strdate
)


class MasterClassBaseIE(InfoExtractor):
    BRIGHTCOVE_URL_TEMPLATE = 'http://players.brightcove.net/%s/default_default/index.html?videoId=%s'
    BRIGHTCOVE_ACCOUNT_ID = '5344802162001'

    def _call_api(self, course_id, csrf, video_id):
        headers = {"Content-Type": "application/vnd.api+json",
                   "X-CSRF-Token": csrf,
                   "Accept": "application/vnd.api+json"}

        return self._download_json('https://www.masterclass.com/jsonapi/v1/courses/%s?include=instructors%%2Cchapters.annotations' % course_id,
                                   video_id, headers=headers, fatal=True)


class MasterClassIE(MasterClassBaseIE):
    IE_NAME = 'masterclass'
    _VALID_URL = r'https?://(?:www\.)?masterclass\.com/classes/(?P<course>[a-z0-9\-]+)/chapters/(?P<id>[a-z0-9\-]+)'
    _TESTS = [{
        'url': 'https://www.masterclass.com/classes/gordon-ramsay-teaches-cooking-restaurant-recipes-at-home/chapters/pomme-puree',
        'md5': '5fbe8736e761c2cc61ed0ee2841e8f47',
        'info_dict': {
            'id': '5834174464001',
            'ext': 'mp4',
            'title': 'GR2_Trailer_v9a_Brightcove_v2',
            'timestamp': 1536792485,
            'upload_date': '20180912',
            'uploader_id': '5344802162001',
            'duration': 93.44
        }
    }]

    def _real_extract(self, url):
        course_id, video_id = re.match(self._VALID_URL, url).groups()
        webpage = self._download_webpage(url, video_id)

        match_free = re.search(r'\"embedUrl\":\"(.+?)\"}</script>', webpage)
        if match_free:  # match free trailer video
            clip_url = match_free.groups()[0]
            return self.url_result(clip_url)

        csrf = self._html_search_regex(r'name=\"csrf-token\" content=\"(.+?)(?=\" \/)', webpage, 'csrf', fatal=True)
        meta = self._call_api(course_id, csrf, video_id)

        chapter = meta.get('data').get('attributes').get('title')
        release_date = unified_strdate(meta.get('data').get('attributes').get('available_at'))
        for json_data in meta['included']:
            json_data = json_data['attributes']
            if (json_data['slug'] == video_id):
                brightcove_id = json_data['brightcove_video_id']
                brightcove_url = self.BRIGHTCOVE_URL_TEMPLATE % (self.BRIGHTCOVE_ACCOUNT_ID, brightcove_id)

                title = json_data['title']
                chapter_number = int_or_none(json_data.get('number'))
                duration = int_or_none(parse_duration(json_data.get('duration')))
                description = json_data.get('abstract')
                thumbnail = url_or_none(json_data.get('video_thumb_url'))

                return ({
                    '_type': 'url_transparent',
                    'url': brightcove_url,
                    'ie_key': BrightcoveNewIE.ie_key(),
                    'id': video_id,
                    'title': title,
                    'chapter': chapter,
                    'chapter_number': chapter_number,
                    'release_date': release_date,
                    'duration': duration,
                    'description': description,
                    'thumbnail': thumbnail
                })


class MasterClassCourseIE(MasterClassBaseIE):
    IE_NAME = "masterclass:course"
    _VALID_URL = r'https?://(?:www\.)?masterclass\.com/classes/(?P<id>[^/]+)'
    _TESTS = [{
        'url': 'https://www.masterclass.com/classes/alicia-keys-teaches-songwriting-and-producing',
        'only_matching': True,
    }, {
        'url': 'https://www.masterclass.com/classes/matthew-walker-teaches-the-science-of-better-sleep',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        course_id = self._match_id(url)
        webpage = self._download_webpage(url, course_id, fatal=True)

        csrf = self._html_search_regex(r'name=\"csrf-token\" content=\"(.+?)(?=\" \/)', webpage, 'csrf', fatal=True)
        meta = self._call_api(course_id, csrf, course_id)

        chapter = meta.get('data').get('attributes').get('title')
        release_date = unified_strdate(meta.get('data').get('attributes').get('available_at'))
        entries = []
        for json_data in meta['included']:
            if (json_data['type'] == 'chapter'):
                json_data = json_data['attributes']
                brightcove_id = json_data['brightcove_video_id']
                brightcove_url = self.BRIGHTCOVE_URL_TEMPLATE % (self.BRIGHTCOVE_ACCOUNT_ID, brightcove_id)

                title = json_data['title']
                video_id = json_data.get('slug')
                chapter_number = int_or_none(json_data.get('number'))
                duration = int_or_none(parse_duration(json_data.get('duration')))
                description = json_data.get('abstract')
                thumbnail = url_or_none(json_data.get('video_thumb_url'))

                entries.append({
                    '_type': 'url_transparent',
                    'url': brightcove_url,
                    'ie_key': BrightcoveNewIE.ie_key(),
                    'id': video_id,
                    'title': title,
                    'chapter': chapter,
                    'chapter_number': chapter_number,
                    'release_date': release_date,
                    'duration': duration,
                    'description': description,
                    'thumbnail': thumbnail
                })

        entries = sorted(entries, key=lambda i: int(i.get("chapter_number")))
        title = meta['data']['attributes']['title']
        description = meta.get('data').get('attributes').get('overview')
        return self.playlist_result(entries, course_id, title, description)
