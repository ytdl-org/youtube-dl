# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
import re


class ScientologyIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?scientology\.tv/series/(?P<series_path>[^/?#]+)/(?P<id>[^/?#]+).html'
    _TEST = {
        'url': 'https://www.scientology.tv/series/l-ron-hubbard-in-his-own-voice/life-as-an-author.html',
        'info_dict': {
            'id': 'life-as-an-author',
            'ext': 'm3u8',
            'title': 'Life as an Author | L. Ron Hubbard: In his Own Voice',
            'description': 'The author on his real life adventures that thrilled millions, to his discoveries behind Dianetics.'
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(r'<title>(.+?)</title>', webpage, 'title').strip()
        description = self._html_search_regex(r'<meta name="description" content="(.+?)" />', webpage, 'description').strip()
        description = re.sub("[^a-zA-Z0-9.,_\s-]+", " ", description)

        # changing address for extration url
        extract_ext = re.search(r'<episode-video>(.*?)</episode-video>', webpage).group(0)
        extract_ext = extract_ext.replace('<episode-video>', '').replace('</episode-video>', '')
        url = url[:url.find('/', 10)] + extract_ext

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'url': url,
        }
