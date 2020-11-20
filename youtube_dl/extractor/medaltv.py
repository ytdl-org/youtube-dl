# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class MedalTvIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?medal\.tv/clips/(?P<id>[0-9]+)/(?P<vid>[a-zA-Z0-9]+)'
    _TEST = {
        'url': 'https://medal.tv/clips/36916370/mkMywBLP93v6',
        'md5': '80c72cd341451078ac5b928d7ef0c895',
        'info_dict': {
            'id': '36916370',
            'ext': 'mp4',
            'title': '1v2 ',
            'thumbnail': 'https://cdn.medal.tv/7570580/thumbnail-36916370-1080p.jpg',
            'uploader': '7570580',
            'timestamp': 1605758297,
            'upload_date': '20201119',
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        hydrationdata = self._parse_json(
            self._search_regex(
                (r'var hydrationData=({.+?})</script>'), webpage, 'hydrationData', default='{}'),
            video_id, fatal=False)

        data = hydrationdata['clips'][video_id]

        thumbnail_dicts = []
        for resolution in ['1080', '720', '480', '360', '240', '144']:
            thumbnail = {
                'id': 'thumbnail{}p'.format(resolution),
                'url': data['thumbnail{}p'.format(resolution)],
                'height': int(resolution),
            }
            thumbnail_dicts.append(thumbnail)

        # Medal badly re-encodes others and/or stretches them. Use native resolution.
        if 'contentUrl1080p' in data:
            url = data['contentUrl1080p']
        else:
            url = data['contentUrl720p']

        return {
            'id': str(data['contentId']),
            'url': url,
            'title': data['contentTitle'],
            'ext': 'mp4',
            # Medal may lose or add a second when reencoding
            'duration': data['videoLengthSeconds'],
            # NB: Display names can change and duplicate. Use uploader/userId for primary keys
            'uploader': str(data['poster']['userId']),
            'uploader_name': data['poster']['displayName'],
            'thumbnails': thumbnail_dicts,
            'thumbnail': data['thumbnail1080p'],
            'timestamp': int(data['created'] / 1000),
        }
