# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class WeiboIE(InfoExtractor):
    """
    The videos in Weibo come from different sites, this IE just finds the link
    to the external video and returns it.
    """
    _VALID_URL = r'https?://video\.weibo\.com/v/weishipin/t_(?P<id>.+?)\.htm'

    _TEST = {
        'url': 'http://video.weibo.com/v/weishipin/t_zjUw2kZ.htm',
        'info_dict': {
            'id': '98322879',
            'ext': 'flv',
            'title': '魔声耳机最新广告“All Eyes On Us”',
        },
        'params': {
            'skip_download': True,
        },
        'add_ie': ['Sina'],
    }

    # Additional example videos from different sites
    # Youku: http://video.weibo.com/v/weishipin/t_zQGDWQ8.htm
    # 56.com: http://video.weibo.com/v/weishipin/t_zQ44HxN.htm

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url, flags=re.VERBOSE)
        video_id = mobj.group('id')
        info_url = 'http://video.weibo.com/?s=v&a=play_list&format=json&mix_video_id=t_%s' % video_id
        info = self._download_json(info_url, video_id)

        videos_urls = map(lambda v: v['play_page_url'], info['result']['data'])
        # Prefer sina video since they have thumbnails
        videos_urls = sorted(videos_urls, key=lambda u: 'video.sina.com' in u)
        player_url = videos_urls[-1]
        m_sina = re.match(r'https?://video\.sina\.com\.cn/v/b/(\d+)-\d+\.html',
                          player_url)
        if m_sina is not None:
            self.to_screen('Sina video detected')
            sina_id = m_sina.group(1)
            player_url = 'http://you.video.sina.com.cn/swf/quotePlayer.swf?vid=%s' % sina_id
        return self.url_result(player_url)
