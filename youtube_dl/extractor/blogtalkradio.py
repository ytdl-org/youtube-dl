from __future__ import unicode_literals

from .common import InfoExtractor


class BlogTalkRadioIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?blogtalkradio\.com/(?:[^/]+/)+(?P<id>[^.]+)'
    _TEST = {
        'url': 'http://www.blogtalkradio.com/ghost/2008/02/20/true-conservative-radio-hosted-by-ghost',
        'md5': '733fdaef2a328f7c8884ac6a33ca0097',
        'info_dict': {
            'id': 'true-conservative-radio-hosted-by-ghost',
            'ext': 'mp3',
            'title': 'True Conservative Radio hosted by Ghost',
            'description': 'free format (political chat)',
            'thumbnail': r're:^https?://.*\.jpg$',
        }
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        title = self._og_search_title(webpage)
        audio_url = self._html_search_meta('twitter:player:stream', webpage, 'audio url')

        return {
            'id': display_id,
            'title': title,
            'url': audio_url,
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
        }
