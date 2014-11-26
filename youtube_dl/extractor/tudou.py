# coding: utf-8

from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor


class TudouIE(InfoExtractor):
    _VALID_URL = r'(?:http://)?(?:www\.)?tudou\.com/(?:listplay|programs|albumplay)/(?:view|(.+?))/(?:([^/]+)|([^/]+))(?:\.html)?'
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
        'url': 'http://www.tudou.com/albumplay/TenTw_JgiPM/PzsAs5usU9A.html',
        'info_dict': {
            'title': 'todo.mp4',
        },
        'add_ie': ['Youku'],
        'skip': 'Only works from China'
    }]

    def _url_for_id(self, id, quality=None):
        info_url = "http://v2.tudou.com/f?id=" + str(id)
        if quality:
            info_url += '&hd' + quality
        webpage = self._download_webpage(info_url, id, "Opening the info webpage")
        final_url = self._html_search_regex('>(.+?)</f>', webpage, 'video url')
        return final_url

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group(2)
        webpage = self._download_webpage(url, video_id)

        m = re.search(r'vcode:\s*[\'"](.+?)[\'"]', webpage)
        if m and m.group(1):
            return {
                '_type': 'url',
                'url': 'youku:' + m.group(1),
                'ie_key': 'Youku'
            }

        title = self._search_regex(
            r",kw:\s*['\"](.+?)[\"']", webpage, 'title')
        thumbnail_url = self._search_regex(
            r",pic:\s*[\"'](.+?)[\"']", webpage, 'thumbnail URL', fatal=False)

        segs_json = self._search_regex(r'segs: \'(.*)\'', webpage, 'segments')
        segments = json.loads(segs_json)
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
            }
            result.append(part_info)

        return result
