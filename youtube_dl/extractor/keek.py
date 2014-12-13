from __future__ import unicode_literals

from .common import InfoExtractor


class KeekIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?keek\.com/(?:!|\w+/keeks/)(?P<id>\w+)'
    IE_NAME = 'keek'
    _TEST = {
        'url': 'https://www.keek.com/ytdl/keeks/NODfbab',
        'md5': '09c5c109067536c1cec8bac8c21fea05',
        'info_dict': {
            'id': 'NODfbab',
            'ext': 'mp4',
            'uploader': 'youtube-dl project',
            'uploader_id': 'ytdl',
            'title': 'test chars: "\'/\\\u00e4<>This is a test video for youtube-dl.For more information, contact phihag@phihag.de .',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        video_url = 'http://cdn.keek.com/keek/video/%s' % video_id
        thumbnail = 'http://cdn.keek.com/keek/thumbnail/%s/w100/h75' % video_id
        webpage = self._download_webpage(url, video_id)

        raw_desc = self._html_search_meta('description', webpage)
        if raw_desc:
            uploader = self._html_search_regex(
                r'Watch (.*?)\s+\(', raw_desc, 'uploader', fatal=False)
            uploader_id = self._html_search_regex(
                r'Watch .*?\(@(.+?)\)', raw_desc, 'uploader_id', fatal=False)
        else:
            uploader = None
            uploader_id = None

        return {
            'id': video_id,
            'url': video_url,
            'ext': 'mp4',
            'title': self._og_search_title(webpage),
            'thumbnail': thumbnail,
            'uploader': uploader,
            'uploader_id': uploader_id,
        }
