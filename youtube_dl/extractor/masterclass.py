# coding: utf-8
from __future__ import unicode_literals

import json
import re

from .brightcove import BrightcoveNewIE


class MasterClassIE(BrightcoveNewIE):
    _VALID_URL = r'https?:\/\/(?:www\.)?masterclass\.com\/classes/\S*$'
    _TESTS = [{
        'url': 'https://www.masterclass.com/classes/gordon-ramsay-teaches-cooking-restaurant-recipes-at-home/chapters/introduction-to-gordon-ramsay',
        'md5': '5fbe8736e761c2cc61ed0ee2841e8f47',
        'info_dict': {
            'id': '5834174464001',
            'ext': 'mp4',
            'title': 'GR2_Trailer_v9a_Brightcove_v2',
            'timestamp': 1536792485,
            'upload_date': '20180912',
            'uploader_id': '5344802162001', }}]

    def __init__(self):
        # need to do this so we can pass the url to BrightcoveNewIE
        self._VALID_URL = BrightcoveNewIE._VALID_URL  # python 2.7 compatible
        # self._VALID_URL = super()._VALID_URL

    def _real_extract(self, url):
        course_id, video_id = re.match(r'https:\/\/www.masterclass.com[\/]classes[\/](.+?)(?=[\/]|$)(?:[\/]chapters)?(?:[\/])?(.+?(?=[?]|$))?', url).groups()

        headers = {"Connection": "keep-alive",
                   "Cache-Control": "max-age=0",
                   "Upgrade-Insecure-Requests": "1"}
        webpage = self._download_webpage(url, course_id, headers=headers)

        match = re.search(r'\"embedUrl\":\"(.+?)\"}</script>', webpage)
        if match:  # free video
            clip_url = match.groups()[0]
            return BrightcoveNewIE._real_extract(self, clip_url)

        csrf = self._html_search_regex(r'name=\"csrf-token\" content=\"(.+?)(?=\" \/)', webpage, 'csrf')
        headers = {"Content-Type": "application/vnd.api+json",
                   "X-CSRF-Token": csrf,
                   "Accept": "application/vnd.api+json"}

        json_url = self._download_json("https://www.masterclass.com/jsonapi/v1/courses/" + course_id + "?include=instructors%2Cchapters%2Cchapters.annotations%2Cchapters.subchapters%2Cpdfs", course_id, headers=headers)
        json_obj = json.dumps(json_url)
        json_data = json.loads(json_obj)

        if video_id:  # non playlist video
            for json_obj in json_data['included']:
                if json_obj['attributes']['slug'] == video_id:
                    brightcove_url = "https://players.brightcove.net/5344802162001/default_default/index.html?videoId=" + json_obj['attributes']['brightcove_video_id']
                    result = BrightcoveNewIE._real_extract(self, brightcove_url)
                    result['chapter_number'] = json_obj['attributes']['number']
                    result['title'] = json_obj['attributes']['title']
                    result['playlist'] = json_data['data']['attributes']['title']
                    return result

        if not video_id and course_id:  # playlist
            entries = []
            for json_obj in json_data['included']:
                if json_obj['type'] == 'chapter':
                    print(str(json_obj['attributes']['number']) + ". ", json_obj['attributes']['title'], json_obj['attributes']['brightcove_video_id'])
                    brightcove_url = "https://players.brightcove.net/5344802162001/default_default/index.html?videoId=" + json_obj['attributes']['brightcove_video_id']

                    result = BrightcoveNewIE._real_extract(self, brightcove_url)
                    result['playlist_index'] = json_obj['attributes']['number']
                    result['title'] = json_obj['attributes']['title']
                    entries.append(result)

            entries = sorted(entries, key=lambda i: int(i['playlist_index']))
            title = json_data['data']['attributes']['title']
            slug = json_data['data']['attributes']['slug']
            description = json_data['data']['attributes']['headline']

            return BrightcoveNewIE.playlist_result(entries, slug, title, description)
