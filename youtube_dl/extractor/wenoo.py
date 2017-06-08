from __future__ import unicode_literals

from .common import InfoExtractor


class WenooIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?wenoo\.net/video/(?P<id>[a-z0-9]+)'
    _TEST = {
        'url': 'http://wenoo.net/video/1f1d1d434f90869367a',
        'md5': 'f41e3b237bc6612554dfa86779a536fd',
        'info_dict': {
            'id': '1f1d1d434f90869367a',
            'ext': 'mp4',
            'title': '[Reupload] Avatar Korra\'s retarded day - 500 Subscriber Milestone video -HD 720p-',
            'description': 'md5:98eabca037057bf4ad529d4fdc3f067b',
            'thumbnail': 're:^http://.*\.jpg$',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        formats = self._parse_html5_media_entries(url,
            webpage, video_id)[0]['formats']

        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'formats': formats,
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
        }
