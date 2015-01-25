# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    unified_strdate,
    int_or_none,
)


class RTL2IE(InfoExtractor):
    """Information Extractor for RTL2"""
    _VALID_URL = r'http?://(?P<url>(?P<domain>(www\.)?rtl2\.de)/.*/(?P<video_id>.*))/'
    _TESTS = [{
            'url': 'http://www.rtl2.de/sendung/grip-das-motormagazin/folge/folge-203-0',
            'info_dict': {
                'id': 'folge-203-0',
                'ext': 'f4v',
                'title': 'GRIP sucht den Sommerkönig',
                'description' : 'Matthias, Det und Helge treten gegeneinander an.'
            },
            'params': {
                # rtmp download
                'skip_download': True,
            },
        },
        {
            'url': 'http://www.rtl2.de/sendung/koeln-50667/video/5512-anna/21040-anna-erwischt-alex/',
            'info_dict': {
                'id': '21040-anna-erwischt-alex',
                'ext': 'mp4',
                'title': 'Anna erwischt Alex!',
                'description' : 'Anna ist Alex\' Tochter bei Köln 50667.'
            },
            'params': {
                # rtmp download
                'skip_download': True,
            },
        },
    ]

    def _real_extract(self, url):
        
        #Some rtl2 urls have no slash at the end, so append it.
        if not url.endswith("/"):
            url += '/'
        
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('video_id')

        webpage = self._download_webpage(url, video_id)

        vico_id = self._html_search_regex(r'vico_id\s*:\s*([0-9]+)', webpage, 'vico_id not found');
        vivi_id = self._html_search_regex(r'vivi_id\s*:\s*([0-9]+)', webpage, 'vivi_id not found');

        info_url = 'http://www.rtl2.de/video/php/get_video.php?vico_id=' + vico_id + '&vivi_id=' + vivi_id
        webpage = self._download_webpage(info_url, '')

        video_info = self._download_json(info_url, video_id)

        download_url = video_info["video"]["streamurl"]
        title = video_info["video"]["titel"]
        description = video_info["video"]["beschreibung"]

        thumbnail = video_info["video"]["image"]

        download_url = download_url.replace("\\", "")

        stream_url = 'mp4:' + self._html_search_regex(r'ondemand/(.*)', download_url, '%s')
        
        #Debug output
        #print('URL: '        + url)
        #print('DL URL: '     + download_url)
        #print('Stream URL: ' + stream_url)
        #print('Title: '      + title)
        #print('Description: '+ description)
        #print('Video ID: '   + video_id)
                
        formats = [{
                'url' : download_url,
                #'app': 'ondemand?_fcs_vhost=cp108781.edgefcs.net',
                'play_path': stream_url,
                'player_url': 'http://www.rtl2.de/flashplayer/vipo_player.swf',
                'page_url': url,
                'flash_version' : "LNX 11,2,202,429",
                'rtmp_conn' : ["S:connect", "O:1", "NS:pageUrl:" + url, "NB:fpad:0", "NN:videoFunction:1", "O:0"],
                'no_resume' : True,
            }]

        return {
            'id': video_id,
            'title': title,
            'thumbnail' : thumbnail,
            'description' : description,
            'formats': formats,
        }
