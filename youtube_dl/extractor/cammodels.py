from __future__ import unicode_literals
from .common import InfoExtractor

class CamModelsIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?cammodels\.com/cam/(?P<id>\w+)'
    _MANIFEST_URL_ROOT_REGEX = r'manifestUrlRoot=(?P<id>https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*))'
    _USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'
    # _TEST = {
    #     'url': 'https://www.cammodels.com/cam/AutumnKnight',
    #     'params': {
    #         'skip_download': True,
    #     },
    #     'skip': _ROOM_OFFLINE,
    #     'info_dict': {
    #         'id': 'AutumnKnight',
    #         'ext': 'flv'
    #     }
    # }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        headers = {
            'User-Agent': self._USER_AGENT
        }
        webpage = self._download_webpage(url_or_request=url, video_id=video_id, headers=headers)
        manifest_url_root = self._html_search_regex(self._MANIFEST_URL_ROOT_REGEX, webpage, 'manifest')
        manifest_url = manifest_url_root + video_id + '.json'
        manifest = self._download_json(manifest_url, video_id=video_id, headers=headers)
        rtmp_formats = manifest['formats']['mp4-rtmp']['encodings']
        formats = []
        for format in rtmp_formats:
            formats.append({
                'ext': 'flv',
                'url': format.get('location'),
                'width': format.get('videoWidth'),
                'height': format.get('videoHeight'),
                'vbr': format.get('videoKbps'),
                'abr': format.get('audioKbps'),
                'format_id': str(format.get('videoWidth'))
            })
        self._sort_formats(formats)
        return {
            'id': video_id,
            'title': self._live_title(video_id),
            'age_limit': self._rta_search(webpage),
            'ext': 'flv',
            'formats': formats
        }