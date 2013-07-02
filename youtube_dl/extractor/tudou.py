# coding: utf-8

import re
import json

from .common import InfoExtractor


class TudouIE(InfoExtractor):
    _VALID_URL = r'(?:http://)?(?:www\.)?tudou\.com/(?:listplay|programs)/(?:view|(.+?))/(?:([^/]+)|([^/]+))(?:\.html)?'
    _TEST = {
        u'url': u'http://www.tudou.com/listplay/zzdE77v6Mmo/2xN2duXMxmw.html',
        u'file': u'159448201.f4v',
        u'md5': u'140a49ed444bd22f93330985d8475fcb',
        u'info_dict': {
            u"title": u"卡马乔国足开大脚长传冲吊集锦"
        }
    }

    def _url_for_id(self, id, quality = None):
        info_url = "http://v2.tudou.com/f?id="+str(id)
        if quality:
            info_url += '&hd' + quality
        webpage = self._download_webpage(info_url, id, "Opening the info webpage")
        final_url = self._html_search_regex('>(.+?)</f>',webpage, 'video url')
        return final_url

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group(2)
        webpage = self._download_webpage(url, video_id)
        title = re.search(",kw:\"(.+)\"",webpage)
        if title is None:
            title = re.search(",kw: \'(.+)\'",webpage)
        title = title.group(1)
        thumbnail_url = re.search(",pic: \'(.+?)\'",webpage)
        if thumbnail_url is None:
            thumbnail_url = re.search(",pic:\"(.+?)\"",webpage)
        thumbnail_url = thumbnail_url.group(1)

        segs_json = self._search_regex(r'segs: \'(.*)\'', webpage, 'segments')
        segments = json.loads(segs_json)
        # It looks like the keys are the arguments that have to be passed as
        # the hd field in the request url, we pick the higher
        quality = sorted(segments.keys())[-1]
        parts = segments[quality]
        result = []
        len_parts = len(parts)
        if len_parts > 1:
            self.to_screen(u'%s: found %s parts' % (video_id, len_parts))
        for part in parts:
            part_id = part['k']
            final_url = self._url_for_id(part_id, quality)
            ext = (final_url.split('?')[0]).split('.')[-1]
            part_info = {'id': part_id,
                          'url': final_url,
                          'ext': ext,
                          'title': title,
                          'thumbnail': thumbnail_url,
                          }
            result.append(part_info)

        return result
