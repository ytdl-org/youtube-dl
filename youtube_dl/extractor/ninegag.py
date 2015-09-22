from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import str_to_int


class NineGagIE(InfoExtractor):
    IE_NAME = '9gag'
    _VALID_URL = r'https?://(?:www\.)?9gag(?:\.com/tv|\.tv)/(?:p|embed)/(?P<id>[a-zA-Z0-9]+)(?:/(?P<display_id>[^?#/]+))?'

    _TESTS = [{
        'url': 'http://9gag.com/tv/p/Kk2X5/people-are-awesome-2013-is-absolutely-awesome',
        'info_dict': {
            'id': 'Kk2X5',
            'ext': 'mp4',
            'description': 'This 3-minute video will make you smile and then make you feel untalented and insignificant. Anyway, you should share this awesomeness. (Thanks, Dino!)',
            'title': '\"People Are Awesome 2013\" Is Absolutely Awesome',
            'uploader_id': 'UCdEH6EjDKwtTe-sO2f0_1XA',
            'uploader': 'CompilationChannel',
            'upload_date': '20131110',
            'view_count': int,
        },
        'add_ie': ['Youtube'],
    }, {
        'url': 'http://9gag.com/tv/p/aKolP3',
        'info_dict': {
            'id': 'aKolP3',
            'ext': 'mp4',
            'title': 'This Guy Travelled 11 countries In 44 days Just To Make This Amazing Video',
            'description': "I just saw more in 1 minute than I've seen in 1 year. This guy's video is epic!!",
            'uploader_id': 'rickmereki',
            'uploader': 'Rick Mereki',
            'upload_date': '20110803',
            'view_count': int,
        },
        'add_ie': ['Vimeo'],
    }, {
        'url': 'http://9gag.com/tv/p/KklwM',
        'only_matching': True,
    }, {
        'url': 'http://9gag.tv/p/Kk2X5',
        'only_matching': True,
    }, {
        'url': 'http://9gag.com/tv/embed/a5Dmvl',
        'only_matching': True,
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
        display_id = mobj.group('display_id') or video_id

        webpage = self._download_webpage(url, display_id)

        post_view = self._parse_json(
            self._search_regex(
                r'var\s+postView\s*=\s*new\s+app\.PostView\({\s*post:\s*({.+?})\s*,\s*posts:\s*prefetchedCurrentPost',
                webpage, 'post view'),
            display_id)

        ie_key = None
        source_url = post_view.get('sourceUrl')
        if not source_url:
            external_video_id = post_view['videoExternalId']
            external_video_provider = post_view['videoExternalProvider']
            source_url = self._EXTERNAL_VIDEO_PROVIDER[external_video_provider]['url'] % external_video_id
            ie_key = self._EXTERNAL_VIDEO_PROVIDER[external_video_provider]['ie_key']
        title = post_view['title']
        description = post_view.get('description')
        view_count = str_to_int(post_view.get('externalView'))
        thumbnail = post_view.get('thumbnail_700w') or post_view.get('ogImageUrl') or post_view.get('thumbnail_300w')

        return {
            '_type': 'url_transparent',
            'url': source_url,
            'ie_key': ie_key,
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'view_count': view_count,
            'thumbnail': thumbnail,
        }
