# coding: utf-8

from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_str


class TudouIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?tudou\.com/(?:listplay|programs(?:/view)?|albumplay)/([^/]+/)*(?P<id>[^/?#]+?)(?:\.html)?/?(?:$|[?#])'
    _TESTS = [{
        'url': 'http://www.tudou.com/listplay/zzdE77v6Mmo/2xN2duXMxmw.html',
        'md5': '140a49ed444bd22f93330985d8475fcb',
        'info_dict': {
            'id': '159448201',
            'ext': 'f4v',
            'title': '卡马乔国足开大脚长传冲吊集锦',
            'thumbnail': 're:^https?://.*\.jpg$',
        }
    }, {
        'url': 'http://www.tudou.com/programs/view/ajX3gyhL0pc/',
        'info_dict': {
            'id': '117049447',
            'ext': 'f4v',
            'title': 'La Sylphide-Bolshoi-Ekaterina Krysanova & Vyacheslav Lopatin 2012',
            'thumbnail': 're:^https?://.*\.jpg$',
        }
    }, {
        'url': 'http://www.tudou.com/albumplay/cJAHGih4yYg.html',
        'only_matching': True,
    }]

    _PLAYER_URL = 'http://js.tudouui.com/bin/lingtong/PortalPlayer_177.swf'

    def _url_for_id(self, video_id, quality=None):
        info_url = 'http://v2.tudou.com/f?id=' + compat_str(video_id)
        if quality:
            info_url += '&hd' + quality
        xml_data = self._download_xml(info_url, video_id, "Opening the info XML page")
        final_url = xml_data.text
        return final_url

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        youku_vcode = self._search_regex(
            r'vcode\s*:\s*[\'"]([^\'"]*)[\'"]', webpage, 'youku vcode', default=None)
        if youku_vcode:
            return self.url_result('youku:' + youku_vcode, ie='Youku')

        title = self._search_regex(
            r',kw\s*:\s*[\'"]([^\'"]+)[\'"]', webpage, 'title')
        thumbnail_url = self._search_regex(
            r',pic\s*:\s*[\'"]([^\'"]+)[\'"]', webpage, 'thumbnail URL', fatal=False)

        player_url = self._search_regex(
            r'playerUrl\s*:\s*[\'"]([^\'"]+\.swf)[\'"]',
            webpage, 'player URL', default=self._PLAYER_URL)

        segments = self._parse_json(self._search_regex(
            r'segs: \'([^\']+)\'', webpage, 'segments'), video_id)
        # It looks like the keys are the arguments that have to be passed as
        # the hd field in the request url, we pick the higher
        # Also, filter non-number qualities (see issue #3643).
        quality = sorted(filter(lambda k: k.isdigit(), segments.keys()),
                         key=lambda k: int(k))[-1]
        parts = segments[quality]
        result = []
        len_parts = len(parts)
        if len_parts > 1:
            self.to_screen('%s: found %s parts' % (video_id, len_parts))
        for part in parts:
            part_id = part['k']
            final_url = self._url_for_id(part_id, quality)
            ext = (final_url.split('?')[0]).split('.')[-1]
            part_info = {
                'id': '%s' % part_id,
                'url': final_url,
                'ext': ext,
                'title': title,
                'thumbnail': thumbnail_url,
                'http_headers': {
                    'Referer': player_url,
                },
            }
            result.append(part_info)

        return {
            '_type': 'multi_video',
            'entries': result,
            'id': video_id,
            'title': title,
        }
