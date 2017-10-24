# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class StretchInternetIE(InfoExtractor):
    IE_DESC = 'StretchInternet'
    _VALID_URL = r'https?://.*?stretchinternet\.com/[^/_?].*(?<=eventId=)(?P<id>.*)(?=&).*'
    _TEST = {
        'url': 'https://portal.stretchinternet.com/umary/portal.htm?eventId=313900&streamType=video',
        'info_dict': {
            'id': '313900',
            'ext': 'mp4',
            'title': 'StretchInternet'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        stream = self._download_json('https://neo-client.stretchinternet.com/streamservice/v1/media/stream/v%s' % video_id, video_id)
        stream_url = stream.get('source')
        return {
            'ie_key': 'Generic',
            'id': video_id,
            'url': 'http://%s' % stream_url,
            'title': 'StretchInternet'
        }
