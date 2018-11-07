# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    str_or_none,
)


class VVVVIDIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?vvvvid\.it/#!(?:show|anime|film|series)/(?P<show_id>\d+)/[^/]+/(?P<season_id>\d+)/(?P<id>[0-9]+)'
    _TESTS = [{
        # video_type == 'video/vvvvid'
        'url': 'https://www.vvvvid.it/#!show/434/perche-dovrei-guardarlo-di-dario-moccia/437/489048/ping-pong',
        'md5': 'b8d3cecc2e981adc3835adf07f6df91b',
        'info_dict': {
            'id': '489048',
            'ext': 'mp4',
            'title': 'Ping Pong',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        # video_type == 'video/rcs'
        'url': 'https://www.vvvvid.it/#!show/376/death-note-live-action/377/482493/episodio-01',
        'md5': '33e0edfba720ad73a8782157fdebc648',
        'info_dict': {
            'id': '482493',
            'ext': 'mp4',
            'title': 'Episodio 01',
        },
        'params': {
            'skip_download': True,
        },
    }]
    _conn_id = None

    def _real_initialize(self):
        self._conn_id = self._download_json(
            'https://www.vvvvid.it/user/login',
            None, headers=self.geo_verification_headers())['data']['conn_id']

    def _real_extract(self, url):
        show_id, season_id, video_id = re.match(self._VALID_URL, url).groups()
        response = self._download_json(
            'https://www.vvvvid.it/vvvvid/ondemand/%s/season/%s' % (show_id, season_id),
            video_id, headers=self.geo_verification_headers(), query={
                'conn_id': self._conn_id,
            })
        if response['result'] == 'error':
            raise ExtractorError('%s said: %s' % (
                self.IE_NAME, response['message']), expected=True)

        vid = int(video_id)
        video_data = list(filter(
            lambda episode: episode.get('video_id') == vid, response['data']))[0]
        formats = []

        # vvvvid embed_info decryption algorithm is reverse engineered from function $ds(h) at vvvvid.js
        def ds(h):
            g = "MNOPIJKL89+/4567UVWXQRSTEFGHABCDcdefYZabstuvopqr0123wxyzklmnghij"

            def f(m):
                l = []
                o = 0
                b = False
                m_len = len(m)
                while ((not b) and o < m_len):
                    n = m[o] << 2
                    o += 1
                    k = -1
                    j = -1
                    if o < m_len:
                        n += m[o] >> 4
                        o += 1
                        if o < m_len:
                            k = (m[o - 1] << 4) & 255
                            k += m[o] >> 2
                            o += 1
                            if o < m_len:
                                j = (m[o - 1] << 6) & 255
                                j += m[o]
                                o += 1
                            else:
                                b = True
                        else:
                            b = True
                    else:
                        b = True
                    l.append(n)
                    if k != -1:
                        l.append(k)
                    if j != -1:
                        l.append(j)
                return l

            c = []
            for e in h:
                c.append(g.index(e))

            c_len = len(c)
            for e in range(c_len * 2 - 1, -1, -1):
                a = c[e % c_len] ^ c[(e + 1) % c_len]
                c[e % c_len] = a

            c = f(c)
            d = ''
            for e in c:
                d += chr(e)

            return d

        for quality in ('_sd', ''):
            embed_code = video_data.get('embed_info' + quality)
            if not embed_code:
                continue
            embed_code = ds(embed_code)
            video_type = video_data.get('video_type')
            if video_type in ('video/rcs', 'video/kenc'):
                embed_code = re.sub(r'https?://([^/]+)/z/', r'https://\1/i/', embed_code).replace('/manifest.f4m', '/master.m3u8')
                if video_type == 'video/kenc':
                    kenc = self._download_json(
                        'https://www.vvvvid.it/kenc', video_id, query={
                            'action': 'kt',
                            'conn_id': self._conn_id,
                            'url': embed_code,
                        }, fatal=False) or {}
                    kenc_message = kenc.get('message')
                    if kenc_message:
                        embed_code += '?' + ds(kenc_message)
                formats.extend(self._extract_m3u8_formats(
                    embed_code, video_id, 'mp4',
                    m3u8_id='hls', fatal=False))
            else:
                formats.extend(self._extract_wowza_formats(
                    'http://sb.top-ix.org/videomg/_definst_/mp4:%s/playlist.m3u8' % embed_code, video_id))
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': video_data['title'],
            'formats': formats,
            'thumbnail': video_data.get('thumbnail'),
            'duration': int_or_none(video_data.get('length')),
            'series': video_data.get('show_title'),
            'season_id': season_id,
            'season_number': video_data.get('season_number'),
            'episode_id': str_or_none(video_data.get('id')),
            'episode_number': int_or_none(video_data.get('number')),
            'episode_title': video_data['title'],
            'view_count': int_or_none(video_data.get('views')),
            'like_count': int_or_none(video_data.get('video_likes')),
        }
