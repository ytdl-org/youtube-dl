# coding: utf-8

import re

from .common import InfoExtractor

class WeiboIE(InfoExtractor):
    """
    The videos in Weibo come from different sites, this IE just finds the link
    to the external video and returns it.
    """
    _VALID_URL = r'https?://video\.weibo\.com/v/weishipin/t_(?P<id>.+?)\.htm'

    _TEST = {
        u'url': u'http://video.weibo.com/v/weishipin/t_zjUw2kZ.htm',
        u'file': u'98322879.flv',
        u'info_dict': {
            u'title': u'魔声耳机最新广告“All Eyes On Us”',
        },
        u'note': u'Sina video',
        u'params': {
            u'skip_download': True,
        },
    }

    # Additional example videos from different sites
    # Youku: http://video.weibo.com/v/weishipin/t_zQGDWQ8.htm
    # 56.com: http://video.weibo.com/v/weishipin/t_zQ44HxN.htm

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url, flags=re.VERBOSE)
        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)
        player_url = self._search_regex(r'var defaultPlayer="(.+?)"', webpage,
                                        u'player url')
        return self.url_result(player_url)

