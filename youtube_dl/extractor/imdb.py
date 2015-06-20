from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..compat import (
    compat_urlparse,
)


class ImdbIE(InfoExtractor):
    IE_NAME = 'imdb'
    IE_DESC = 'Internet Movie Database trailers'
    _VALID_URL = r'http://(?:www|m)\.imdb\.com/video/imdb/vi(?P<id>\d+)'

    _TEST = {
        'url': 'http://www.imdb.com/video/imdb/vi2524815897',
        'info_dict': {
            'id': '2524815897',
            'ext': 'mp4',
            'title': 'Ice Age: Continental Drift Trailer (No. 2) - IMDb',
            'description': 'md5:9061c2219254e5d14e03c25c98e96a81',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage('http://www.imdb.com/video/imdb/vi%s' % video_id, video_id)
        descr = self._html_search_regex(
            r'(?s)<span itemprop="description">(.*?)</span>',
            webpage, 'description', fatal=False)
        available_formats = re.findall(
            r'case \'(?P<f_id>.*?)\' :$\s+url = \'(?P<path>.*?)\'', webpage,
            flags=re.MULTILINE)
        formats = []
        for f_id, f_path in available_formats:
            f_path = f_path.strip()
            format_page = self._download_webpage(
                compat_urlparse.urljoin(url, f_path),
                'Downloading info for %s format' % f_id)
            json_data = self._search_regex(
                r'<script[^>]+class="imdb-player-data"[^>]*?>(.*?)</script>',
                format_page, 'json data', flags=re.DOTALL)
            info = json.loads(json_data)
            format_info = info['videoPlayerObject']['video']
            formats.append({
                'format_id': f_id,
                'url': format_info['videoInfoList'][0]['videoUrl'],
            })

        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'formats': formats,
            'description': descr,
            'thumbnail': format_info['slate'],
        }


class ImdbListIE(InfoExtractor):
    IE_NAME = 'imdb:list'
    IE_DESC = 'Internet Movie Database lists'
    _VALID_URL = r'http://www\.imdb\.com/list/(?P<id>[\da-zA-Z_-]{11})'
    _TEST = {
        'url': 'http://www.imdb.com/list/JFs9NWw6XI0',
        'info_dict': {
            'id': 'JFs9NWw6XI0',
            'title': 'March 23, 2012 Releases',
        },
        'playlist_count': 7,
    }

    def _real_extract(self, url):
        list_id = self._match_id(url)
        webpage = self._download_webpage(url, list_id)
        entries = [
            self.url_result('http://www.imdb.com' + m, 'Imdb')
            for m in re.findall(r'href="(/video/imdb/vi[^"]+)"\s+data-type="playlist"', webpage)]

        list_title = self._html_search_regex(
            r'<h1 class="header">(.*?)</h1>', webpage, 'list title')

        return self.playlist_result(entries, list_id, list_title)
