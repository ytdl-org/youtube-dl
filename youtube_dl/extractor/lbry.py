# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class LBRYIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?lbry\.tv/@(?P<uploader_url>[^/?#&]+:[0-9a-f]+)/(?P<title_url>[^/?#&]+:[0-9a-f]+)'
    _TEST = {
        'url': 'https://lbry.tv/@MimirsBrunnr:8/sunne-light-of-the-world-summer-solstice:6',
        'md5': '18e0cf991d0a9db3e23e979c20ed40a1',
        'info_dict': {
            'id': '62b95f07397a291d16e911ce7eb7c816a6992202',
            'ext': 'mp4',
            'title': 'Sunne, Light of the World (Summer Solstice)',
            'title_url': 'sunne-light-of-the-world-summer-solstice:6',
            'thumbnail': 'https://thumbnails.lbry.com/gtsvh8nQLHA',
            'uploader': 'Mimir\'s Brunnr',
            'uploader_url': 'MimirsBrunnr:8'
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        uploader_url = mobj.group('uploader_url')
        title_url = mobj.group('title_url')

        webpage = self._download_webpage('https://lbry.tv/@%s/%s' % (uploader_url, title_url), uploader_url + '+' + title_url)
        webpage_uploader = self._download_webpage('https://lbry.tv/@%s' % uploader_url, uploader_url)

        title = self._html_search_regex(r'<title>(.*?)</title>', webpage, 'title', default=None) or \
            self._og_search_property('title', webpage)
        thumbnail = self._og_search_property('image', webpage)
        uploader = self._html_search_regex(r'<title>(.*?)</title>', webpage_uploader, 'uploader', default=None) or \
            self._og_search_property('title', webpage_uploader)

        embed_url = self._og_search_property('video', webpage, default=None) or \
            self._og_search_property('video:secure_url', webpage, default=None) or \
            self._og_search_property('twitter:player', webpage)

        video_id = embed_url.split('/')[-1]

        video_type = self._og_search_property('video:type', webpage)
        video_ext = video_type.replace('video/', '')

        format_url = embed_url.replace('lbry.tv/$/embed', 'player.lbry.tv/content/claims') + '/stream?download=1'
        formats = [{'ext': video_ext, 'url': format_url, 'vcodec': 'h264', 'acodec': 'aac'}]

        return {
            'id': video_id,
            'ext': video_ext,
            'title': title,
            'title_url': title_url,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'uploader_url': uploader_url,
            'formats': formats,
        }
