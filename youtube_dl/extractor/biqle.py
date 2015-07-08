# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

import re

class BiqleIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?biqle\.ru/watch/(?P<id>-?[0-9]+_[0-9]+)'
    _TEST = {
        'url': 'http://www.biqle.ru/watch/847655_160197695',
        'md5': 'ad5f746a874ccded7b8f211aeea96637',
        'info_dict': {
            'id': '847655_160197695',
            'ext': 'mp4',
            'title': 'Foo Fighters - The Pretender (Live at Wembley Stadium) — BIQLE Видео'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        
        chr_index = video_id.find('_')
        oid = video_id[:chr_index]
        vid = video_id[chr_index + 1:]
    
        title = self._html_search_regex(r'<title>(.*?)</title>', webpage, 'title')
        
        foo = self._html_search_regex(r'<iframe id="video_player"(.*?)></iframe>', webpage, 'foo')
        embed_hash = self._search_regex(r'hash=(.*?)&', foo, 'embed_hash')
        api_url = "https://api.vk.com/method/video.getEmbed?oid=" + oid + "&video_id=" + vid + "&embed_hash=" + embed_hash + "&callback=daxabAjaxFn"
        vk_api = self._download_webpage(api_url, "vk.com api")
        
        url240 = self._search_regex(r'"url240":"(.*?.mp4)', vk_api, 'url240', fatal=False)
        url360 = self._search_regex(r'"url360":"(.*?.mp4)', vk_api, 'url360', fatal=False)
        url480 = self._search_regex(r'"url480":"(.*?.mp4)', vk_api, 'url480', fatal=False)
        url720 = self._search_regex(r'"url720":"(.*?.mp4)', vk_api, 'url720', fatal=False)
        
        formats = []
        
        if(url240 != None):
            formats.append({
                'url': re.sub(r'\\', '', url240),
                'format':'240p mp4'
            })
        if(url360 != None):
            formats.append({
                'url': re.sub(r'\\', '', url360),
                'format':'360p mp4'
            })
        if(url480 != None):
            formats.append({
                'url': re.sub(r'\\', '', url480),
                'format':'480p mp4'
            })
        if(url720 != None):
            formats.append({
                'url': re.sub(r'\\', '', url720),
                'format':'720p mp4'
            })
        
        return {
            'id': video_id,
            'title': title,
            'formats': formats
        }