# coding: utf-8

import re
import json

from .common import InfoExtractor

class WeiboIE(InfoExtractor):
    """
    The videos in Weibo come from different sites, this IE just finds the link
    to the external video and returns it.
    """
    _VALID_URL = r'https?://video\.weibo\.com/v/weishipin/t_(?P<id>.+?)\.htm'

    _TEST = {
        u'add_ie': ['Sina'],
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
        info_url = 'http://video.weibo.com/?s=v&a=play_list&format=json&mix_video_id=t_%s' % video_id
        info_page = self._download_webpage(info_url, video_id)
        info = json.loads(info_page)

        videos_urls = map(lambda v: v['play_page_url'], info['result']['data'])
        #Prefer sina video since they have thumbnails
        videos_urls = sorted(videos_urls, key=lambda u: u'video.sina.com' in u)
        player_url = videos_urls[-1]
        m_sina = re.match(r'https?://video.sina.com.cn/v/b/(\d+)-\d+.html', player_url)
        if m_sina is not None:
            self.to_screen('Sina video detected')
            sina_id = m_sina.group(1)
            player_url = 'http://you.video.sina.com.cn/swf/quotePlayer.swf?vid=%s' % sina_id
        return self.url_result(player_url)

