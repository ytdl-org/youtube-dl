# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    compat_urllib_request,
    compat_urllib_parse,
    compat_urllib_parse_urlparse,
    ExtractorError,
)


class CeskaTelevizeIE(InfoExtractor):
    _VALID_URL = r'https?://www\.ceskatelevize\.cz/(porady|ivysilani)/(.+/)?(?P<id>[^?#]+)'

    _TESTS = [
        {
            'url': 'http://www.ceskatelevize.cz/ivysilani/10532695142-prvni-republika/213512120230004-spanelska-chripka',
            'info_dict': {
                'id': '213512120230004',
                'ext': 'flv',
                'title': 'První republika: Španělská chřipka',
                'duration': 3107.4,
            },
            'params': {
                'skip_download': True,  # requires rtmpdump
            },
            'skip': 'Works only from Czech Republic.',
        },
        {
            'url': 'http://www.ceskatelevize.cz/ivysilani/1030584952-tsatsiki-maminka-a-policajt',
            'info_dict': {
                'id': '20138143440',
                'ext': 'flv',
                'title': 'Tsatsiki, maminka a policajt',
                'duration': 6754.1,
            },
            'params': {
                'skip_download': True,  # requires rtmpdump
            },
            'skip': 'Works only from Czech Republic.',
        },
        {
            'url': 'http://www.ceskatelevize.cz/ivysilani/10532695142-prvni-republika/bonus/14716-zpevacka-z-duparny-bobina',
            'info_dict': {
                'id': '14716',
                'ext': 'flv',
                'title': 'První republika: Zpěvačka z Dupárny Bobina',
                'duration': 90,
            },
            'params': {
                'skip_download': True,  # requires rtmpdump
            },
        },
    ]

    def _real_extract(self, url):
        url = url.replace('/porady/', '/ivysilani/').replace('/video/', '')

        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)

        NOT_AVAILABLE_STRING = 'This content is not available at your territory due to limited copyright.'
        if '%s</p>' % NOT_AVAILABLE_STRING in webpage:
            raise ExtractorError(NOT_AVAILABLE_STRING, expected=True)

        typ = self._html_search_regex(r'getPlaylistUrl\(\[\{"type":"(.+?)","id":".+?"\}\],', webpage, 'type')
        episode_id = self._html_search_regex(r'getPlaylistUrl\(\[\{"type":".+?","id":"(.+?)"\}\],', webpage, 'episode_id')

        data = {
            'playlist[0][type]': typ,
            'playlist[0][id]': episode_id,
            'requestUrl': compat_urllib_parse_urlparse(url).path,
            'requestSource': 'iVysilani',
        }

        req = compat_urllib_request.Request('http://www.ceskatelevize.cz/ivysilani/ajax/get-playlist-url',
                                            data=compat_urllib_parse.urlencode(data))

        req.add_header('Content-type', 'application/x-www-form-urlencoded')
        req.add_header('x-addr', '127.0.0.1')
        req.add_header('X-Requested-With', 'XMLHttpRequest')
        req.add_header('Referer', url)

        playlistpage = self._download_json(req, video_id)

        req = compat_urllib_request.Request(compat_urllib_parse.unquote(playlistpage['url']))
        req.add_header('Referer', url)

        playlist = self._download_xml(req, video_id)

        formats = []
        for i in playlist.find('smilRoot/body'):
            if 'AD' not in i.attrib['id']:
                base_url = i.attrib['base']
                parsedurl = compat_urllib_parse_urlparse(base_url)
                duration = i.attrib['duration']

                for video in i.findall('video'):
                    if video.attrib['label'] != 'AD':
                        format_id = video.attrib['label']
                        play_path = video.attrib['src']
                        vbr = int(video.attrib['system-bitrate'])

                        formats.append({
                            'format_id': format_id,
                            'url': base_url,
                            'vbr': vbr,
                            'play_path': play_path,
                            'app': parsedurl.path[1:] + '?' + parsedurl.query,
                            'rtmp_live': True,
                            'ext': 'flv',
                        })

        self._sort_formats(formats)

        return {
            'id': episode_id,
            'title': self._html_search_regex(r'<title>(.+?) — iVysílání — Česká televize</title>', webpage, 'title'),
            'duration': float(duration),
            'formats': formats,
        }
