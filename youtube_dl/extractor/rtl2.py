# encoding: utf-8
from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    unified_strdate,
    int_or_none,
)


class RTL2IE(InfoExtractor):
    """Information Extractor for RTL NOW, RTL2 NOW, RTL NITRO, SUPER RTL NOW, VOX NOW and n-tv NOW"""
    _VALID_URL = r'http?://(?P<url>(?P<domain>(www\.)?rtl2\.de)/.*/(?P<video_id>.*))'
    _TESTS = [{
            'url': 'http://www.rtl2.de/sendung/grip-das-motormagazin/folge/folge-203-0',
            'info_dict': {
                'id': 'folge-203-0',
                'ext': 'f4v',
                'title': 'GRIP sucht den Sommerk\xf6nig',
                'description' : 'Matthias, Det und Helge treten gegeneinander an.'
            },
            'params': {
                # rtmp download
                #'skip_download': True,
            },
        },
        {
            'url': 'http://www.rtl2.de/sendung/koeln-50667/video/5512-anna/21040-anna-erwischt-alex/',
            'info_dict': {
                'id': '21040-anna-erwischt-alex',
                'ext': 'f4v',
                'title': 'GRIP sucht den Sommerk\xf6nig',
                'description' : 'Matthias, Det und Helge treten gegeneinander an.'
            },
            'params': {
                # rtmp download
                #'skip_download': True,
            },
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_page_url = 'http://%s/' % mobj.group('domain')
        video_id = mobj.group('video_id')
    
        webpage = self._download_webpage('http://' + mobj.group('url'), video_id)

        vico_id = self._html_search_regex(r'vico_id\s*:\s*([0-9]+)', webpage, '%s');
        vivi_id = self._html_search_regex(r'vivi_id\s*:\s*([0-9]+)', webpage, '%s');

        info_url = 'http://www.rtl2.de/video/php/get_video.php?vico_id=' + vico_id + '&vivi_id=' + vivi_id
        webpage = self._download_webpage(info_url, '')

        video_info = json.loads(webpage)

        download_url = video_info["video"]["streamurl"] # self._html_search_regex(r'streamurl\":\"(.*?)\"', webpage, '%s');
        title = video_info["video"]["titel"] # self._html_search_regex(r'titel\":\"(.*?)\"', webpage, '%s');
        description = video_info["video"]["beschreibung"] # self._html_search_regex(r'beschreibung\":\"(.*?)\"', webpage, '%s');
        #ext = self._html_search_regex(r'streamurl\":\".*?(\..{2,4})\"', webpage, '%s');

        thumbnail = video_info["video"]["image"]

        download_url = download_url.replace("\\", "")

        stream_url = 'mp4:' + self._html_search_regex(r'ondemand/(.*)', download_url, '%s')

        #print(download_url)
        #print(stream_url)
        #print(title)
        #print(description)
        #print(video_id)
        
        formats = []

        fmt = {
            'url' : download_url,
                #'app': 'ondemand?_fcs_vhost=cp108781.edgefcs.net',
                'play_path': stream_url,
                'player_url': 'http://www.rtl2.de/flashplayer/vipo_player.swf',
                'page_url': url,
                'flash_version' : "LNX 11,2,202,429",
                'rtmp_conn' : ["S:connect", "O:1", "NS:pageUrl:" + url, "NB:fpad:0", "NN:videoFunction:1", "O:0"],
                'no_resume' : 1,
        }

        formats.append(fmt)

        return {
            'id': video_id,
            'title': title,
            'thumbnail' : thumbnail,
            'description' : description,
            'formats': formats,
        }
