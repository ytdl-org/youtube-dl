# coding: utf-8
from __future__ import unicode_literals

import base64
import binascii
import json
import os
import random

from .common import InfoExtractor
from ..aes import aes_cbc_decrypt
from ..compat import (
    compat_HTTPError,
    compat_b64decode,
    compat_ord,
)
from ..utils import (
    bytes_to_intlist,
    bytes_to_long,
    ExtractorError,
    float_or_none,
    int_or_none,
    intlist_to_bytes,
    long_to_bytes,
    pkcs1pad,
    strip_or_none,
    unified_strdate,
    urljoin,
)


class ADNIE(InfoExtractor):
    IE_DESC = 'Anime Digital Network'
    _VALID_URL = r'https?://(?:www\.)?animedigitalnetwork\.fr/video/[^/]+/(?P<id>\d+)'
    _TEST = {
        'url': 'http://animedigitalnetwork.fr/video/blue-exorcist-kyoto-saga/7778-episode-1-debut-des-hostilites',
        'md5': '0319c99885ff5547565cacb4f3f9348d',
        'info_dict': {
            'id': '7778',
            'ext': 'mp4',
            'title': 'Blue Exorcist - Kyôto Saga - Episode 1',
            'description': 'md5:2f7b5aa76edbc1a7a92cedcda8a528d5',
        }
    }

    _BASE_URL = 'http://animedigitalnetwork.fr'
    _API_BASE_URL = 'https://gw.api.animedigitalnetwork.fr'
    _RSA_KEY = (0x9B42B08905199A5CCE2026274399CA560ECB209EE9878A708B1C0812E1BB8CB5D1FB7441861147C1A1F2F3A0476DD63A9CAC20D3E983613346850AA6CB38F16DC7D720FD7D86FC6E5B3D5BBC72E14CD0BF9E869F2CEA2CCAD648F1DCE38F1FF916CEFB2D339B64AA0264372344BC775E265E8A852F88144AB0BD9AA06C1A4ABB, 65537)
    _POS_ALIGN_MAP = {
        'start': 1,
        'end': 3,
    }
    _LINE_ALIGN_MAP = {
        'middle': 8,
        'end': 4,
    }

    @staticmethod
    def _ass_subtitles_timecode(seconds):
        return '%01d:%02d:%02d.%02d' % (seconds / 3600, (seconds % 3600) / 60, seconds % 60, (seconds % 1) * 100)

    def _get_subtitles(self, sub_path, video_id):
        if not sub_path:
            return None

        enc_subtitles = self._download_webpage(
            urljoin(self._BASE_URL, sub_path),
            video_id, 'Downloading subtitles location', fatal=False) or '{}'
        subtitle_location = (self._parse_json(enc_subtitles, video_id, fatal=False) or {}).get('location')
        if subtitle_location:
            enc_subtitles = self._download_webpage(
                urljoin(self._BASE_URL, subtitle_location),
                video_id, 'Downloading subtitles data', fatal=False,
                headers={'Origin': 'https://animedigitalnetwork.fr'})
        if not enc_subtitles:
            return None

        # http://animedigitalnetwork.fr/components/com_vodvideo/videojs/adn-vjs.min.js
        dec_subtitles = intlist_to_bytes(aes_cbc_decrypt(
            bytes_to_intlist(compat_b64decode(enc_subtitles[24:])),
            bytes_to_intlist(binascii.unhexlify(self._K + '4b8ef13ec1872730')),
            bytes_to_intlist(compat_b64decode(enc_subtitles[:24]))
        ))
        subtitles_json = self._parse_json(
            dec_subtitles[:-compat_ord(dec_subtitles[-1])].decode(),
            None, fatal=False)
        if not subtitles_json:
            return None

        subtitles = {}
        for sub_lang, sub in subtitles_json.items():
            ssa = '''[Script Info]
ScriptType:V4.00
[V4 Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,TertiaryColour,BackColour,Bold,Italic,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,AlphaLevel,Encoding
Style: Default,Arial,18,16777215,16777215,16777215,0,-1,0,1,1,0,2,20,20,20,0,0
[Events]
Format: Marked,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text'''
            for current in sub:
                start, end, text, line_align, position_align = (
                    float_or_none(current.get('startTime')),
                    float_or_none(current.get('endTime')),
                    current.get('text'), current.get('lineAlign'),
                    current.get('positionAlign'))
                if start is None or end is None or text is None:
                    continue
                alignment = self._POS_ALIGN_MAP.get(position_align, 2) + self._LINE_ALIGN_MAP.get(line_align, 0)
                ssa += os.linesep + 'Dialogue: Marked=0,%s,%s,Default,,0,0,0,,%s%s' % (
                    self._ass_subtitles_timecode(start),
                    self._ass_subtitles_timecode(end),
                    '{\\a%d}' % alignment if alignment != 2 else '',
                    text.replace('\n', '\\N').replace('<i>', '{\\i1}').replace('</i>', '{\\i0}'))

            if sub_lang == 'vostf':
                sub_lang = 'fr'
            subtitles.setdefault(sub_lang, []).extend([{
                'ext': 'json',
                'data': json.dumps(sub),
            }, {
                'ext': 'ssa',
                'data': ssa,
            }])
        return subtitles

    def _real_extract(self, url):
        video_id = self._match_id(url)
        config_url = self._API_BASE_URL + '/player/video/%s/configuration' % video_id
        player_config = self._download_json(
            config_url, video_id,
            'Downloading player config JSON metadata')['player']['options']

        user = player_config['user']
        if not user.get('hasAccess'):
            raise ExtractorError('This video is only available for paying users')
            # self.raise_login_required() # FIXME: Login is not implemented

        token = self._download_json(
            user.get('refreshTokenUrl') or (self._API_BASE_URL + '/player/refresh/token'),
            video_id, 'Downloading access token', headers={'x-player-refresh-token': user['refreshToken']},
            data=b'')['token']

        links_url = player_config.get('videoUrl') or (self._API_BASE_URL + '/player/video/%s/link' % video_id)
        self._K = ''.join([random.choice('0123456789abcdef') for _ in range(16)])
        message = bytes_to_intlist(json.dumps({
            'k': self._K,
            't': token,
        }))

        # Sometimes authentication fails for no good reason, retry with
        # a different random padding
        links_data = None
        for _ in range(3):
            padded_message = intlist_to_bytes(pkcs1pad(message, 128))
            n, e = self._RSA_KEY
            encrypted_message = long_to_bytes(pow(bytes_to_long(padded_message), e, n))
            authorization = base64.b64encode(encrypted_message).decode()

            try:
                links_data = self._download_json(
                    urljoin(self._BASE_URL, links_url), video_id,
                    'Downloading links JSON metadata', headers={
                        'X-Player-Token': authorization
                    },
                    query={
                        'freeWithAds': 'true',
                        'adaptive': 'false',
                        'withMetadata': 'true',
                        'source': 'Web'
                    }
                )
                break
            except ExtractorError as e:
                if not isinstance(e.cause, compat_HTTPError):
                    raise e

                if e.cause.code == 401:
                    # This usually goes away with a different random pkcs1pad, so retry
                    continue

                error = self._parse_json(e.cause.read(), video_id)
                message = error.get('message')
                if e.cause.code == 403 and error.get('code') == 'player-bad-geolocation-country':
                    self.raise_geo_restricted(msg=message)
                else:
                    raise ExtractorError(message)
        else:
            raise ExtractorError('Giving up retrying')

        links = links_data.get('links') or {}
        metas = links_data.get('metadata') or {}
        sub_path = (links.get('subtitles') or {}).get('all')
        video_info = links_data.get('video') or {}

        formats = []
        for format_id, qualities in (links.get('streaming') or {}).items():
            if not isinstance(qualities, dict):
                continue
            for quality, load_balancer_url in qualities.items():
                load_balancer_data = self._download_json(
                    load_balancer_url, video_id,
                    'Downloading %s %s JSON metadata' % (format_id, quality),
                    fatal=False) or {}
                m3u8_url = load_balancer_data.get('location')
                if not m3u8_url:
                    continue
                m3u8_formats = self._extract_m3u8_formats(
                    m3u8_url, video_id, 'mp4', 'm3u8_native',
                    m3u8_id=format_id, fatal=False)
                if format_id == 'vf':
                    for f in m3u8_formats:
                        f['language'] = 'fr'
                formats.extend(m3u8_formats)
        self._sort_formats(formats)

        video = (self._download_json(self._API_BASE_URL + '/video/%s' % video_id, video_id,
                                     'Downloading additional video metadata', fatal=False) or {}).get('video')
        show = video.get('show') or {}

        return {
            'id': video_id,
            'title': metas.get('title') or video_id,
            'description': strip_or_none(metas.get('summary') or video.get('summary')),
            'thumbnail': video_info.get('image'),
            'formats': formats,
            'subtitles': sub_path and self.extract_subtitles(sub_path, video_id),
            'episode': metas.get('subtitle') or video.get('name'),
            'episode_number': int_or_none(video.get('shortNumber')),
            'series': video_info.get('playlistTitle') or show.get('title'),
            'season_number': int_or_none(video.get('season')),
            'duration': int_or_none(video_info.get('duration') or video.get('duration')),
            'release_date': unified_strdate(video.get('release_date')),
            'average_rating': video.get('rating') or metas.get('rating'),
            'comment_count': int_or_none(video.get('commentsCount')),
        }
