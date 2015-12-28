# encoding: utf-8
from __future__ import unicode_literals

import re
from .common import InfoExtractor


class RTL2IE(InfoExtractor):
    _VALID_URL = r'http?://(?:www\.)?rtl2\.de/[^?#]*?/(?P<id>[^?#/]*?)(?:$|/(?:$|[?#]))'
    _TESTS = [{
        'url': 'http://www.rtl2.de/sendung/grip-das-motormagazin/folge/folge-203-0',
        'info_dict': {
            'id': 'folge-203-0',
            'ext': 'f4v',
            'title': 'GRIP sucht den Sommerkönig',
            'description': 'Matthias, Det und Helge treten gegeneinander an.'
        },
        'params': {
            # rtmp download
            'skip_download': True,
        },
    }, {
        'url': 'http://www.rtl2.de/sendung/koeln-50667/video/5512-anna/21040-anna-erwischt-alex/',
        'info_dict': {
            'id': '21040-anna-erwischt-alex',
            'ext': 'mp4',
            'title': 'Anna erwischt Alex!',
            'description': 'Anna ist Alex\' Tochter bei Köln 50667.'
        },
        'params': {
            # rtmp download
            'skip_download': True,
        },
    }]

    def _real_extract(self, url):
        # Some rtl2 urls have no slash at the end, so append it.
        if not url.endswith('/'):
            url += '/'

        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        mobj = re.search(
            r'<div[^>]+data-collection="(?P<vico_id>\d+)"[^>]+data-video="(?P<vivi_id>\d+)"',
            webpage)
        if mobj:
            vico_id = mobj.group('vico_id')
            vivi_id = mobj.group('vivi_id')
        else:
            vico_id = self._html_search_regex(
                r'vico_id\s*:\s*([0-9]+)', webpage, 'vico_id')
            vivi_id = self._html_search_regex(
                r'vivi_id\s*:\s*([0-9]+)', webpage, 'vivi_id')
        info_url = 'http://www.rtl2.de/video/php/get_video.php?vico_id=' + vico_id + '&vivi_id=' + vivi_id

        info = self._download_json(info_url, video_id)
        video_info = info['video']
        title = video_info['titel']
        description = video_info.get('beschreibung')
        thumbnail = video_info.get('image')

        download_url = video_info['streamurl']
        download_url = download_url.replace('\\', '')
        stream_url = 'mp4:' + self._html_search_regex(r'ondemand/(.*)', download_url, 'stream URL')
        rtmp_conn = ["S:connect", "O:1", "NS:pageUrl:" + url, "NB:fpad:0", "NN:videoFunction:1", "O:0"]

        formats = [{
            'url': download_url,
            'play_path': stream_url,
            'player_url': 'http://www.rtl2.de/flashplayer/vipo_player.swf',
            'page_url': url,
            'flash_version': 'LNX 11,2,202,429',
            'rtmp_conn': rtmp_conn,
            'no_resume': True,
        }]
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'description': description,
            'formats': formats,
        }
