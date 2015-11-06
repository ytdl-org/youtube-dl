# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
import re
import string


class VidziIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?vidzi\.tv/(?P<id>\w+)'
    _TEST = {
        'url': 'http://vidzi.tv/cghql9yq6emu.html',
        'md5': '4f16c71ca0c8c8635ab6932b5f3f1660',
        'info_dict': {
            'id': 'cghql9yq6emu',
            'ext': 'mp4',
            'title': 'youtube-dl test video  1\\\\2\'3/4<5\\\\6ä7↭',
        },
    }

    def int2base(self, x, base):
        digs = string.digits + string.ascii_letters
        if x < 0:
            sign = -1
        elif x == 0:
            return digs[0]
        else:
            sign = 1
        x *= sign
        digits = []
        while x:
            digits.append(digs[x % base])
            x = x // base
        if sign < 0:
            digits.append('-')
        digits.reverse()
        return ''.join(digits)

    def unpack_packer(self, p, a, c, k, s):
        k = k.split(s)
        for i in range(int(c) - 1, 1, -1):
            p = re.sub('\\b' + self.int2base(i, int(a)) + '\\b', k[i], p)
        return p

    def unpack(self, content):
        packers = re.findall(r'function\(p,a,c,k,e,d\){.+}\(\'.*\',\d+,\d+,\'[^\']+\'\.split\(\'.\'\)', content)
        for (packer) in packers:
            p, a, c, k, s = re.search(r'function\(p,a,c,k,e,d\){.+}\(\'(.*)\',(\d+),(\d+),\'([^\']+)\'\.split\(\'(.)\'\)', packer).groups()
            content = content.replace(packer, self.unpack_packer(p, a, c, k, s))
        return content

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)
        webpage = self.unpack(webpage)
        video_url = self._html_search_regex(
            r'{\s*file\s*:\s*"([^"]+)"\s*}', webpage, 'video url')
        title = self._html_search_regex(
            r'(?s)<h2 class="video-title">(.*?)</h2>', webpage, 'title')

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
        }
