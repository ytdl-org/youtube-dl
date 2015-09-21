from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..utils import str_to_int


class NineGagIE(InfoExtractor):
    IE_NAME = '9gag'
    _VALID_URL = r'https?://(?:www\.)?9gag\.com/tv/p/(?P<id>[a-zA-Z0-9]+)/(?P<display_id>[^?#/]+)'

    _TESTS = [{
        "url": "http://9gag.com/tv/p/Kk2X5/people-are-awesome-2013-is-absolutely-awesome",
        "info_dict": {
            "id": "Kk2X5",
            "ext": "mp4",
            "description": "This 3-minute video will make you smile and then make you feel untalented and insignificant. Anyway, you should share this awesomeness. (Thanks, Dino!)",
            "title": "\"People Are Awesome 2013\" Is Absolutely Awesome",
            'uploader_id': 'UCdEH6EjDKwtTe-sO2f0_1XA',
            'uploader': 'CompilationChannel',
            'upload_date': '20131110',
            "view_count": int,
            "thumbnail": "re:^https?://",
        },
        'add_ie': ['Youtube']
    }, {
        'url': 'http://9gag.com/tv/p/KklwM/alternate-banned-opening-scene-of-gravity?ref=fsidebar',
        'info_dict': {
            'id': 'KklwM',
            'ext': 'mp4',
            'display_id': 'alternate-banned-opening-scene-of-gravity',
            "description": "While Gravity was a pretty awesome movie already, YouTuber Krishna Shenoi came up with a way to improve upon it, introducing a much better solution to Sandra Bullock's seemingly endless tumble in space. The ending is priceless.",
            'title': "Banned Opening Scene Of \"Gravity\" That Changes The Whole Movie",
            'uploader': 'Krishna Shenoi',
            'upload_date': '20140401',
            'uploader_id': 'krishnashenoi93',
        },
        'add_ie': ['Youtube']
    }]
    _EXTERNAL_VIDEO_PROVIDER = {
        '1': {
            'url': '%s',
            'ie_key': 'Youtube',
        },
        '2': {
            'url': 'http://player.vimeo.com/video/%s',
            'ie_key': 'Vimeo',
        },
        '3': {
            'url': 'http://instagram.com/p/%s',
            'ie_key': 'Instagram',
        },
        '4': {
            'url': 'http://vine.co/v/%s',
            'ie_key': 'Vine',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        display_id = mobj.group('display_id')

        webpage = self._download_webpage(url, display_id)

        post_view = json.loads(self._html_search_regex(
            r'var postView = new app\.PostView\({\s*post:\s*({.+?}),\s*posts:\s*prefetchedCurrentPost', webpage, 'post view'))

        external_video_id = post_view['videoExternalId']
        external_video_provider = post_view['videoExternalProvider']
        title = post_view['title']
        description = post_view['description']
        view_count = str_to_int(post_view['externalView'])
        thumbnail = post_view.get('thumbnail_700w') or post_view.get('ogImageUrl') or post_view.get('thumbnail_300w')

        return {
            '_type': 'url_transparent',
            'url': self._EXTERNAL_VIDEO_PROVIDER[external_video_provider]['url'] % external_video_id,
            'ie_key': self._EXTERNAL_VIDEO_PROVIDER[external_video_provider]['ie_key'],
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'view_count': view_count,
            'thumbnail': thumbnail,
        }
