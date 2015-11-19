from __future__ import unicode_literals

import re

from .common import InfoExtractor


class BloombergIE(InfoExtractor):
    _VALID_URL = r'https?://www\.bloomberg\.com/news/[^/]+/[^/]+/(?P<id>[^/?#]+)'

    _TESTS = [{
        'url': 'http://www.bloomberg.com/news/videos/b/aaeae121-5949-481e-a1ce-4562db6f5df2',
        # The md5 checksum changes
        'info_dict': {
            'id': 'qurhIVlJSB6hzkVi229d8g',
            'ext': 'flv',
            'title': 'Shah\'s Presentation on Foreign-Exchange Strategies',
            'description': 'md5:a8ba0302912d03d246979735c17d2761',
        },
    }, {
        'url': 'http://www.bloomberg.com/news/articles/2015-11-12/five-strange-things-that-have-been-happening-in-financial-markets',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        name = self._match_id(url)
        webpage = self._download_webpage(url, name)
        video_id = self._search_regex(r'"bmmrId":"(.+?)"', webpage, 'id')
        title = re.sub(': Video$', '', self._og_search_title(webpage))

        embed_info = self._download_json(
            'http://www.bloomberg.com/api/embed?id=%s' % video_id, video_id)
        formats = []
        for stream in embed_info['streams']:
            if stream["muxing_format"] == "TS":
                formats.extend(self._extract_m3u8_formats(stream['url'], video_id))
            else:
                formats.extend(self._extract_f4m_formats(stream['url'], video_id))
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
        }
