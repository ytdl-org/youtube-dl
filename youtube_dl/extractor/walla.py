# coding: utf-8
from __future__ import unicode_literals


import re

from .common import InfoExtractor


class WallaIE(InfoExtractor):
    _VALID_URL = r'http://vod\.walla\.co\.il/\w+/(?P<id>\d+)'
    _TEST = {
        'url': 'http://vod.walla.co.il/movie/2642630/one-direction-all-for-one',
        'info_dict': {
            'id': '2642630',
            'ext': 'flv',
            'title': 'וואן דיירקשן: ההיסטריה',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        
        video_id = mobj.group('id')

        config_url = 'http://video2.walla.co.il/?w=null/null/%s/@@/video/flv_pl' % video_id
        
        webpage = self._download_webpage(config_url, video_id, '')

        media_id = self._html_search_regex(r'<media_id>(\d+)</media_id>', webpage, video_id, 'extract media id')

        prefix = '0' if len(media_id) == 7 else ''

        series =  '%s%s' % (prefix, media_id[0:2])
        session = media_id[2:5]
        episode = media_id[5:7]
        
        title = self._html_search_regex(r'<title>(.*)</title>', webpage, video_id, 'title')

        default_quality = self._html_search_regex(r'<qualities defaultType="(\d+)">', webpage, video_id, 0)

        quality = default_quality if default_quality else '40'

        media_path = '/%s/%s/%s' % (series, session, media_id) #self._html_search_regex(r'<quality type="%s">.*<src>(.*)</src>' % default_quality ,webpage, '', flags=re.DOTALL) 

        playpath = 'mp4:media/%s/%s/%s-%s' % (series, session, media_id, quality) #self._html_search_regex(r'<quality type="%s">.*<src>(.*)</src>' % default_quality ,webpage, '', flags=re.DOTALL) 

        subtitles = {}

        subtitle_url = self._html_search_regex(r'<subtitles.*<src>(.*)</src>.*</subtitle>', webpage, video_id, 0)

        print subtitle_url

        if subtitle_url:
            subtitles_page = self._download_webpage(subtitle_url, video_id, '')
            subtitles['heb'] = subtitles_page

        return {
            'id': video_id,
            'title': title,
            'url': 'rtmp://wafla.walla.co.il:1935/vod',
            'player_url': 'http://isc.walla.co.il/w9/swf/video_swf/vod/WallaMediaPlayerAvod.swf',
            'page_url': url,
            'app': "vod",
            'play_path': playpath,
            'tc_url': 'rtmp://wafla.walla.co.il:1935/vod',
            'rtmp_protocol': 'rtmp',
            'ext': 'flv',
            'subtitles': subtitles,
        }