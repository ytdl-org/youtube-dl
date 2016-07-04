# coding: utf-8
from __future__ import unicode_literals

import re
import itertools

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    unified_strdate,
)


class VineIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?vine\.co/(?:v|oembed)/(?P<id>\w+)'
    _TESTS = [{
        'url': 'https://vine.co/v/b9KOOWX7HUx',
        'md5': '2f36fed6235b16da96ce9b4dc890940d',
        'info_dict': {
            'id': 'b9KOOWX7HUx',
            'ext': 'mp4',
            'title': 'Chicken.',
            'alt_title': 'Vine by Jack Dorsey',
            'upload_date': '20130519',
            'uploader': 'Jack Dorsey',
            'uploader_id': '76',
            'view_count': int,
            'like_count': int,
            'comment_count': int,
            'repost_count': int,
        },
    }, {
        'url': 'https://vine.co/v/MYxVapFvz2z',
        'md5': '7b9a7cbc76734424ff942eb52c8f1065',
        'info_dict': {
            'id': 'MYxVapFvz2z',
            'ext': 'mp4',
            'title': 'Fuck Da Police #Mikebrown #justice #ferguson #prayforferguson #protesting #NMOS14',
            'alt_title': 'Vine by Mars Ruiz',
            'upload_date': '20140815',
            'uploader': 'Mars Ruiz',
            'uploader_id': '1102363502380728320',
            'view_count': int,
            'like_count': int,
            'comment_count': int,
            'repost_count': int,
        },
    }, {
        'url': 'https://vine.co/v/bxVjBbZlPUH',
        'md5': 'ea27decea3fa670625aac92771a96b73',
        'info_dict': {
            'id': 'bxVjBbZlPUH',
            'ext': 'mp4',
            'title': '#mw3 #ac130 #killcam #angelofdeath',
            'alt_title': 'Vine by Z3k3',
            'upload_date': '20130430',
            'uploader': 'Z3k3',
            'uploader_id': '936470460173008896',
            'view_count': int,
            'like_count': int,
            'comment_count': int,
            'repost_count': int,
        },
    }, {
        'url': 'https://vine.co/oembed/MYxVapFvz2z.json',
        'only_matching': True,
    }, {
        'url': 'https://vine.co/v/e192BnZnZ9V',
        'info_dict': {
            'id': 'e192BnZnZ9V',
            'ext': 'mp4',
            'title': 'ยิ้ม~ เขิน~ อาย~ น่าร้ากอ้ะ >//< @n_whitewo @orlameena #lovesicktheseries  #lovesickseason2',
            'alt_title': 'Vine by Pimry_zaa',
            'upload_date': '20150705',
            'uploader': 'Pimry_zaa',
            'uploader_id': '1135760698325307392',
            'view_count': int,
            'like_count': int,
            'comment_count': int,
            'repost_count': int,
        },
        'params': {
            'skip_download': True,
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage('https://vine.co/v/' + video_id, video_id)

        data = self._parse_json(
            self._search_regex(
                r'window\.POST_DATA\s*=\s*({.+?});\s*</script>',
                webpage, 'vine data'),
            video_id)

        data = data[list(data.keys())[0]]

        formats = [{
            'format_id': '%(format)s-%(rate)s' % f,
            'vcodec': f.get('format'),
            'quality': f.get('rate'),
            'url': f['videoUrl'],
        } for f in data['videoUrls'] if f.get('videoUrl')]

        self._sort_formats(formats)

        username = data.get('username')

        return {
            'id': video_id,
            'title': data.get('description') or self._og_search_title(webpage),
            'alt_title': 'Vine by %s' % username if username else self._og_search_description(webpage, default=None),
            'thumbnail': data.get('thumbnailUrl'),
            'upload_date': unified_strdate(data.get('created')),
            'uploader': username,
            'uploader_id': data.get('userIdStr'),
            'view_count': int_or_none(data.get('loops', {}).get('count')),
            'like_count': int_or_none(data.get('likes', {}).get('count')),
            'comment_count': int_or_none(data.get('comments', {}).get('count')),
            'repost_count': int_or_none(data.get('reposts', {}).get('count')),
            'formats': formats,
        }


class VineUserIE(InfoExtractor):
    IE_NAME = 'vine:user'
    _VALID_URL = r'(?:https?://)?vine\.co/(?P<u>u/)?(?P<user>[^/]+)/?(\?.*)?$'
    _VINE_BASE_URL = 'https://vine.co/'
    _TESTS = [
        {
            'url': 'https://vine.co/Visa',
            'info_dict': {
                'id': 'Visa',
            },
            'playlist_mincount': 46,
        },
        {
            'url': 'https://vine.co/u/941705360593584128',
            'only_matching': True,
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        user = mobj.group('user')
        u = mobj.group('u')

        profile_url = '%sapi/users/profiles/%s%s' % (
            self._VINE_BASE_URL, 'vanity/' if not u else '', user)
        profile_data = self._download_json(
            profile_url, user, note='Downloading user profile data')

        user_id = profile_data['data']['userId']
        timeline_data = []
        for pagenum in itertools.count(1):
            timeline_url = '%sapi/timelines/users/%s?page=%s&size=100' % (
                self._VINE_BASE_URL, user_id, pagenum)
            timeline_page = self._download_json(
                timeline_url, user, note='Downloading page %d' % pagenum)
            timeline_data.extend(timeline_page['data']['records'])
            if timeline_page['data']['nextPage'] is None:
                break

        entries = [
            self.url_result(e['permalinkUrl'], 'Vine') for e in timeline_data]
        return self.playlist_result(entries, user)
