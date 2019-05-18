# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class MQubeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?mqube\.net/play/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://mqube.net/play/20181228624995',
        'md5': 'b5ec46773f7b7c5286d3ed3c85faab92',
        'info_dict': {
            'id': '20181228624995',
            'ext': 'wav',
            'title': 'deaky',
            'thumbnail': r're:^https?://.*\.gif(\?.+?)$',
            'description': 'mih',
            'uploader_id': 'muraokamayuko',
            'views': int,
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

        audio_url = self._search_regex(r'<audio controls id=(["\'])smart-audio\1 preload=\'true\' src=\'(?P<audio_url>.+?)\'></audio>', webpage, 'audio_url', group='audio_url', fatal=False)
        title = self._search_regex(r'<div class=(["\'])item-title\1>(?P<title>.+?)</div>', webpage, 'title', group='title', fatal=False)
        uploader_id = self._search_regex(r'<a class=(["\'])all-items\1 href=\1/user/(?P<uploader_id>.+?)\1>', webpage, 'uploader_id', group='uploader_id', fatal=False)
        # uploader = self._search_regex(r'<a[^>]+class=(["\'])all-items\1[^>]*>(?P<uploader>[^<]+)', webpage, 'uploader', group='uploader', fatal=False)
        views = int(self._search_regex(r'<span[^>]+class=(["\'])ajax-pv-counter num-font\1[^>]*>(?P<views>[^<]+)', webpage, 'view_count', group='views', fatal=False))
        description = self._og_search_description(webpage)
        thumbnail = self._og_search_thumbnail(webpage)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'uploader_id': uploader_id,
            'views': views,
            'url': audio_url,
            # TODO more properties (see youtube_dl/extractor/common.py)
        }
