# coding: utf-8
from __future__ import unicode_literals
import urllib
import ast

from .common import InfoExtractor


class ArstechnicaIE(InfoExtractor):
    _VALID_URL = r'https?://(www.)?arstechnica.com/[a-z]+/[0-9]+/[0-9]+/(?P<id>[-a-z0-9]+)/??'
    _TEST = {
        'url': 'http://arstechnica.com/security/2015/09/video-3d-printed-tsa-travel-sentry-keys-really-do-open-tsa-locks/',
        'md5': 'd07dc4dd168a8bc7bf782dac7ad691db',
        'info_dict': {
            'id': 'video-3d-printed-tsa-travel-sentry-keys-really-do-open-tsa-locks',
            'ext': 'mp4',
            'title': '3D printed TSA Travel Sentry keys really do open TSA locks',
            'thumbnail': 're:^https?://.*\.jpg$',
            'description': 'We downloaded the models from GitHub, tweaked, printed, and gained access.',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        protocol = url.split("://")[0]

        title = self._html_search_regex(r'<h1[a-z\"\= ]+>(?:Video: )*(.*?)</h1>', webpage, 'title')

        initial_js_url = protocol + ":" + self._html_search_regex(r'<script src="(.*)" class="x-skip"></script>', webpage, 'initial_js_url')
        initial_js_content = self._download_webpage(initial_js_url, video_id)

        loader_js_url = self._search_regex(r"var url = \\'([a-z:/.?]+)\\'", initial_js_content, 'loader_js_url')
        params = {
            'videoId': self._search_regex(r"videoId: \\'([a-z0-9]+)\\'", initial_js_content, 'videoId'),
            'playerId': self._search_regex(r"playerId: \\'([a-z0-9]+)\\'", initial_js_content, 'playerId'),
            'target': self._search_regex(r"target: \\'([a-z0-9]+)\\'", initial_js_content, 'target'),
        }
        loader_js_url = "%s%s" % (loader_js_url, urllib.urlencode(params))
        loader_js_content = self._download_webpage(loader_js_url, video_id)

        sources_list = ast.literal_eval(self._search_regex(r'"sources":\[(.*)\],"thumb', loader_js_content, 'sources_list'))

        formats = []

        for source in sources_list:
            formats.append({
                'format_id': source['type'],
                'url': source['src'],
                'quality': source['quality'],
            })

        return {
            'id': video_id,
            'title': title,
            'description': self._og_search_description(webpage),
            'formats': formats,
            'thumbnail': self._search_regex(r'"thumb_path":"(.*)","title', loader_js_content, 'thumb_path'),
        }
