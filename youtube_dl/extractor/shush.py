# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import (
    compat_parse_qs,
)
from ..utils import (
    encode_dict,
    sanitized_Request,
    urlencode_postdata,
)


class ShushIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?shush\.se/(?:index\.php)?\?(?P<id>id=[0-9]+&show=.+)'
    _TEST = {
        'url': 'http://www.shush.se/index.php?id=23&show=thirdwatch',
        'md5': '13d99f581a174b82e239b85720cbfa2a',
        'info_dict': {
            'id': '23-thirdwatch',
            'ext': 'mp4',
            'title': 'Third Watch Season 2 Episode: 1 – The Lost',
            'thumbnail': 're:^https?://.*\.(gif|jpg)$',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        parsed_id = compat_parse_qs(video_id)
        if parsed_id:
            video_id = "%s-%s" % (parsed_id['id'][0], parsed_id['show'][0])

        webpage = self._download_webpage(url, video_id)

        title = self._search_regex(r'<title>Shush.se - Watch (.+?) \| Free Online Streaming', webpage, 'title')
        query_id = self._html_search_regex(r'\{link:"([a-zA-Z0-9@/!=]+)",image:', webpage, 'query_id')

        file_info_request = sanitized_Request('http://www.shush.se/plugins/load.php')
        file_info_request.add_header("Content-type", 'application/x-www-form-urlencoded')
        file_info_request.data = urlencode_postdata(encode_dict({'link': query_id}))
        file_info = self._download_json(file_info_request, video_id)

        return {
            'id': video_id,
            'title': title,
            'url': file_info["link"],
            'ext': file_info["type"],
            'thumbnail': file_info["image"],
        }
