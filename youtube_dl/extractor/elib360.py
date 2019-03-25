# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import (
    compat_str,
)
import re


class Elib360IE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?360elib\.com:2029/Details.aspx\?voiceid=(?P<voc_id>[0-9]+)&childid=(?P<cld_id>[0-9]+)'
    _TEST = {
        'url': 'http://www.360elib.com:2029/Details.aspx?voiceid=10732&childid=617839###',
        'md5': '0e5d06001e72fdc44b008bee0735d5f7',
        'info_dict': {
            'id': '10732_617839',
            'ext': 'm4a',
            'title': '明朝那些事儿03',
            'description': '明朝那些事儿03',
        }
    }

    @classmethod
    def _match_group(cls, group, url):
        m = cls._VALID_URL_RE.match(url)
        assert m
        return compat_str(m.group(group))

    def _real_extract(self, url):
        voice_id = self._match_group("voc_id", url)
        child_id = self._match_group("cld_id", url)
        video_id = voice_id + "_" + child_id
        webpage = self._download_webpage(url, video_id)
        print(webpage)
        src = self._search_regex(r'<source[^>]+src=[\'"]([^"]+?)[\'"][^>]*?>', webpage, 'src', fatal=False, flags=re.UNICODE)

        title = self._search_regex(r'<span[^>]+id=[\'"]ctl00_ContentPlaceHolder1_lb_childname[\'"][^>]*?>([^<]+)', webpage, 'title', fatal=False, flags=re.UNICODE)
        title = title.strip()
        return {
            'id': video_id,
            'title': title,
            'description': title,
            'formats': [{
                'url': "http://www.360elib.com:2029" + src
            }]
        }
