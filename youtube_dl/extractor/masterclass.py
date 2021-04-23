# coding: utf-8
from __future__ import unicode_literals
import re

from .brightcove import BrightcoveNewIE
from .common import InfoExtractor


class MasterClassIE(InfoExtractor):
    IE_NAME = 'masterclass'
    _VALID_URL = r'https:\/\/www.masterclass.com[\/]classes[\/](.+?)(?=[\/]|$)(?:[\/]chapters)?(?:[\/])?(.+?(?=[?]|$))?'
    _TESTS = [{
        'url': 'https://www.masterclass.com/classes/gordon-ramsay-teaches-cooking-restaurant-recipes-at-home/chapters/introduction-to-gordon-ramsay',
        'md5': '5fbe8736e761c2cc61ed0ee2841e8f47',
        'info_dict': {
            'id': '5834174464001',
            'ext': 'mp4',
            'title': 'GR2_Trailer_v9a_Brightcove_v2',
            'timestamp': 1536792485,
            'upload_date': '20180912',
            'uploader_id': '5344802162001',
        },
        'skip': 'Requires masterclass account credentials',
    }]

    BRIGHTCOVE_URL_TEMPLATE = 'http://players.brightcove.net/%s/default_default/index.html?videoId=%s'
    BRIGHTCOVE_ACCOUNT_ID = '5344802162001'

    def _real_extract(self, url):
        course_id, video_id = re.match(self._VALID_URL, url).groups()

        headers = {"Connection": "keep-alive",
                   "Cache-Control": "max-age=0",
                   "Upgrade-Insecure-Requests": "1"}
        webpage = self._download_webpage(url, course_id, headers=headers)

        match_free = re.search(r'\"embedUrl\":\"(.+?)\"}</script>', webpage)

        if match_free:  # match free video
            clip_url = match_free.groups()[0]
            return self.url_result(clip_url)

        csrf = self._html_search_regex(r'name=\"csrf-token\" content=\"(.+?)(?=\" \/)', webpage, 'csrf')
        headers = {"Content-Type": "application/vnd.api+json",
                   "X-CSRF-Token": csrf,
                   "Accept": "application/vnd.api+json"}

        json_data = self._download_json('https://www.masterclass.com/jsonapi/v1/courses/%s?include=instructors%%2Cchapters%%2Cchapters.annotations%%2Cchapters.subchapters%%2Cpdfs' % course_id, course_id, headers=headers)

        entries = []
        for json_obj in json_data.get('included'):
            if (video_id and json_obj.get('attributes').get('slug') == video_id) or (not video_id and json_obj.get('type') == 'chapter'):
                brightcove_id = json_obj.get('attributes').get('brightcove_video_id')
                brightcove_url = self.BRIGHTCOVE_URL_TEMPLATE % (self.BRIGHTCOVE_ACCOUNT_ID, brightcove_id)

                title = json_obj.get('attributes').get('title')
                playlist = json_data.get('data').get('attributes').get('title')
                playlist_index = json_obj.get('attributes').get('number')

                entries.append({
                    '_type': 'url_transparent',
                    'url': brightcove_url,
                    'ie_key': BrightcoveNewIE.ie_key(),
                    'id': brightcove_id,
                    'title': title,
                    'playlist': playlist,
                    'playlist_index': playlist_index
                })

        if video_id and len(entries) == 1:
            return entries[0]
        elif not video_id:
            entries = sorted(entries, key=lambda i: int(i['playlist_index']))
            title = json_data.get('data').get('attributes').get('title')
            slug = json_data.get('data').get('attributes').get('slug')
            description = json_data.get('data').get('attributes').get('headline')
            return self.playlist_result(entries, slug, title, description)
