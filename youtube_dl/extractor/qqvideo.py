# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class QqVideoIE(InfoExtractor):
    IE_NAME = 'qq'
    IE_DESC = '腾讯'
    # http://v.qq.com/page/9/n/6/9jWRYWGYvn6.html
    # http://v.qq.com/cover/o/oy8cl3wkrebcv8h.html?vid=x001970x491
    _VALID_URL = r'http://v\.qq\.com/(?:cover/.+?\.html\?vid=(?P<vid>[\w\d]+)|page/.+?/(?P<id>[\w\d]+)\.html)'
    _TESTS = [{
        'url': 'http://v.qq.com/page/9/n/6/9jWRYWGYvn6.html',
        'info_dict': {
            'id': '9jWRYWGYvn6',
            'ext': 'mp4',
            'title': '歼-20试飞63次 国防部指挥例行试验',
        }
    },
        {
            'url': 'http://v.qq.com/cover/o/oy8cl3wkrebcv8h.html?vid=x001970x491',
            'info_dict': {
                'id': 'x001970x491',
                'ext': 'mp4',
                'title': '韩国青瓦台召开紧急会议 国防部加紧检查战备状态',
            },
        }
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        if (video_id is None):
            video_id = mobj.group('vid')

        info_doc = self._download_xml(
                'http://vv.video.qq.com/getinfo?vid=%s&otype=xml&platform=1' % video_id,
                video_id, 'fetch video metadata')

        title = info_doc.find('./vl/vi/ti').text

        url_doc = self._download_xml(
                'http://vv.video.qq.com/geturl?vid=%s&otype=xml&platform=1' % video_id,
                video_id, 'fetch video url')

        url = url_doc.find('./vd/vi/url').text
        ext = self._search_regex('\.([\d\w]+)\?', url, '', '')

        return {
            'id': video_id,
            'title': title,
            'url': url,
            'ext': ext,
        }
