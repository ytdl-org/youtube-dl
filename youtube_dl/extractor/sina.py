# coding: utf-8

import re
import xml.etree.ElementTree

from .common import InfoExtractor
from ..utils import (
    compat_urllib_request,
    compat_urllib_parse,
)


class SinaIE(InfoExtractor):
    _VALID_URL = r'''https?://(.*?\.)?video\.sina\.com\.cn/
                        (
                            (.+?/(((?P<pseudo_id>\d+).html)|(.*?(\#|(vid=))(?P<id>\d+?)($|&))))
                            |
                            # This is used by external sites like Weibo
                            (api/sinawebApi/outplay.php/(?P<token>.+?)\.swf)
                        )
                  '''

    _TEST = {
        u'url': u'http://video.sina.com.cn/news/vlist/zt/chczlj2013/?opsubject_id=top12#110028898',
        u'file': u'110028898.flv',
        u'md5': u'd65dd22ddcf44e38ce2bf58a10c3e71f',
        u'info_dict': {
            u'title': u'《中国新闻》 朝鲜要求巴拿马立即释放被扣船员',
        }
    }

    @classmethod
    def suitable(cls, url):
        return re.match(cls._VALID_URL, url, flags=re.VERBOSE) is not None

    def _extract_video(self, video_id):
        data = compat_urllib_parse.urlencode({'vid': video_id})
        url_page = self._download_webpage('http://v.iask.com/v_play.php?%s' % data,
            video_id, u'Downloading video url')
        image_page = self._download_webpage(
            'http://interface.video.sina.com.cn/interface/common/getVideoImage.php?%s' % data,
            video_id, u'Downloading thumbnail info')
        url_doc = xml.etree.ElementTree.fromstring(url_page.encode('utf-8'))

        return {'id': video_id,
                'url': url_doc.find('./durl/url').text,
                'ext': 'flv',
                'title': url_doc.find('./vname').text,
                'thumbnail': image_page.split('=')[1],
                }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url, flags=re.VERBOSE)
        video_id = mobj.group('id')
        if mobj.group('token') is not None:
            # The video id is in the redirected url
            self.to_screen(u'Getting video id')
            request = compat_urllib_request.Request(url)
            request.get_method = lambda: 'HEAD'
            (_, urlh) = self._download_webpage_handle(request, 'NA', False)
            return self._real_extract(urlh.geturl())
        elif video_id is None:
            pseudo_id = mobj.group('pseudo_id')
            webpage = self._download_webpage(url, pseudo_id)
            video_id = self._search_regex(r'vid:\'(\d+?)\'', webpage, u'video id')

        return self._extract_video(video_id)
