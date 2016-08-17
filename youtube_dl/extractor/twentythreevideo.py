from __future__ import unicode_literals

from .common import InfoExtractor


class TwentyThreeVideoIE(InfoExtractor):
    IE_NAME = '23video'
    _VALID_URL = r'https?://(?:www\.)?(?P<client>[\w-]+)\.23video\.com/v.ihtml/player.html.*photo_id=(?P<id>\d+)'
    _TEST = {}

    _URL_TEMPLATE = 'https://%s.23video.com/%s/%s/%s/%s/download-video.mp4'
    _FORMATS = {
        'video_hd': {
            'width': 1280,
            'height': 720,
        },
        'video_medium': {
            'width': 640,
            'height': 360,
        },
        'video_mobile_high': {
            'width': 320,
            'height': 180,
        }
    }

    def _extract_formats(self, url, client_id):
        client_name = self._search_regex(r'([a-z]+)\.23video\.com', url, 'client name')
        video_id = self._search_regex(r'photo%5fid=([^?&]+)', url, 'video id')
        token = self._search_regex(r'token=([^?&]+)', url, 'token')

        formats = []
        for format_key in self._FORMATS.keys():
            formats.append({
                'url': self._URL_TEMPLATE % (client_name, client_id, video_id,
                    token, format_key),
                'width': self._FORMATS.get(format_key, {}).get('width'),
                'height': self._FORMATS.get(format_key, {}).get('height'),
            })

        return formats

    def _real_extract(self, url):
        # TODO: Find out how to extract client_id
        raise NotImplementedError('Not able to extract the `client_id`')
