# coding: utf-8
from __future__ import unicode_literals
from .common import InfoExtractor
from ..compat import compat_urlparse


class YoutunerIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?youtuner\.co/s/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://youtuner.co/s/149379',
        'md5': '1f9672e4c264f374101ded6a41e2540a',
        'info_dict': {
            'id': '149379',
            'ext': 'mp3',
            'title': 'Anime Crazies episódio 100! - Como tudo começou?',
            'uploader': 'Anime Crazies',
            'thumbnail': r're:^https?://.*\.jpg$',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)
        thumbnail = "{0.scheme}://{0.netloc}/{1}".format(compat_urlparse.urlsplit(url), self._search_regex(r"<hgroup[^>]*>[^<]+<div[^>]+style=\"[^']+'([^']+)'", webpage, 'thumbnail'))
        title = self._html_search_regex(r'<h1>(.+?)</h1>', webpage, 'title')
        url = self._html_search_regex(r'<a[^>]+href=\"([^>]*)\"[^>]*>Baixar', webpage, 'url')
        return {
            'id': video_id,
            'title': title,
            'uploader': self._search_regex(r'<p[^>]+class=\"entry-meta\"[^>]*>[^<]+<a[^<]+>([^<]+)<', webpage, 'uploader', fatal=False),
            'url': url,
            'thumbnail': thumbnail,
        }
