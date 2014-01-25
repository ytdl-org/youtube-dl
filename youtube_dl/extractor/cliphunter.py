import re
import string

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    ExtractorError,
)

translation_table = (
    '\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f\x10\x11\x12'
    '\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f !"#:%.\'=)*+,-./0123'
    '456789:;</>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]&_`hbcevofhdjknamoutsstupwrli{'
    '|}~\x7f\x80\x81\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x8c\x8d\x8e\x8f'
    '\x90\x91\x92\x93\x94\x95\x96\x97\x98\x99\x9a\x9b\x9c\x9d\x9e\x9f\xa0\xa1'
    '\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xab\xac\xad\xae\xaf\xb0\xb1\xb2\xb3'
    '\xb4\xb5\xb6\xb7\xb8\xb9\xba\xbb\xbc\xbd\xbe\xbf\xc0\xc1\xc2\xc3\xc4\xc5'
    '\xc6\xc7\xc8\xc9\xca\xcb\xcc\xcd\xce\xcf\xd0\xd1\xd2\xd3\xd4\xd5\xd6\xd7'
    '\xd8\xd9\xda\xdb\xdc\xdd\xde\xdf\xe0\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9'
    '\xea\xeb\xec\xed\xee\xef\xf0\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xfb'
    '\xfc\xfd\xfe\xff'
)


class CliphunterIE(InfoExtractor):
    """Information Extractor for Cliphunter"""
    IE_NAME = u'cliphunter'

    _VALID_URL = (r'(?:http://)?(?:www\.)?cliphunter\.com/w/'
                  '(?P<id>[0-9]+)/'
                  '(?P<seo>.+?)(?:\?.*)?')
    _TESTS = [{
        u'url': u'http://www.cliphunter.com/w/1012420/Fun_Jynx_Maze_solo',
        u'file': u'1012420.flv',
        u'md5': u'49f72e2fd2977e6e518be9836dcf861e',
        u'info_dict': {
            u"title": u"Fun Jynx Maze solo",
        }
    },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Unable to extract media URL')

        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)

        pl_fiji = re.search(r'pl_fiji = \'([^\']+)\'', webpage).group(1)
        pl_c_qual = re.search(r'pl_c_qual = "(.)"', webpage).group(1)
        video_title = re.search(r'mediaTitle = "([^"]+)"', webpage).group(1)

        video_url = string.translate(pl_fiji.encode(), translation_table)

        formats = [{
            'url': video_url,
            'ext': determine_ext(video_url),
            'format': pl_c_qual,
            'format_id': pl_c_qual,
        }]

        return {
            'id': video_id,
            'title': video_title,
            'formats': formats,
            'description': '',
        }
