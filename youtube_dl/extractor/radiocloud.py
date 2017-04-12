# coding: utf-8
from __future__ import unicode_literals
import re

from .common import InfoExtractor

from ..utils import (
    ExtractorError,
    extract_attributes,
    get_elements_by_class,
)


class RadioCloudIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?radiocloud\.jp/archive/.*?content_id=(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://radiocloud.jp/archive/so?content_id=13165',
        'md5': '6f97afc008931d72c21db1331dbdce94',
        'info_dict': {
            'id': '13165',
            'ext': 'm4a',
            'title': '毒蝮三太夫のミュージックプレゼント：千葉県市川市鬼高『お酒の専門店「酒壱番」』編',
            'description': '1/16(月)放送(11:20～11:40頃)から。訪問先は、千葉県市川市鬼高3-15−5『お酒の専門店「酒壱番」』さん。47年続く国民的中継番組のトーク部分のみをお楽しみください。',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        def get_input_by_name(html, name):
            for e in re.finditer(r'<input.*?>', html):
                a = extract_attributes(e.group())
                if a.get('name') == name:
                    return a.get('value')
            return None

        element = None
        for e in get_elements_by_class('contents_box', webpage):
            if get_input_by_name(e, 'content_id') == video_id:
                element = e
                break

        if not element:
            raise ExtractorError('Could not find details of id %s' % video_id)

        file_url = get_input_by_name(element, 'file_url')
        if not file_url:
            raise ExtractorError('Could not find player URL')
        file_url = 'https:' + file_url

        title = get_input_by_name(element, 'title')
        if not title:
            title = self._html_search_regex(r'<span>(.+?)</span>', element, 'title')
        description = self._html_search_regex(r'<div>(.+?)</div>', element,
                                              'description', fatal=False)

        webpage = self._download_webpage(file_url, video_id,
                                         headers={'Referer': url},
                                         note='Downloading player',
                                         errnote='Unable to download player')

        file_url = self._search_regex(r'var\s+source\s*=\s*"(.+?)"', webpage, 'url')

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'url': file_url
        }
