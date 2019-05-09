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
    compat_b64decode,
    compat_ord,
)
from ..utils import (
    bytes_to_intlist,
    bytes_to_long,
    ExtractorError,
    float_or_none,
    intlist_to_bytes,
    long_to_bytes,
    pkcs1pad,
    strip_or_none,
    urljoin,
)


class ADNIE(InfoExtractor):
    IE_DESC = 'Anime Digital Network'
    _VALID_URL = r'https?://(?:www\.)?animedigitalnetwork\.fr/video/[^/]+/(?P<id>\d+)'
    _TEST = {
        'url': 'http://animedigitalnetwork.fr/video/blue-exorcist-kyoto-saga/7778-episode-1-debut-des-hostilites',
        'md5': 'e497370d847fd79d9d4c74be55575c7a',
        'info_dict': {
            'id': '7778',
            'ext': 'mp4',
            'title': 'Blue Exorcist - Kyôto Saga - Épisode 1',
            'description': 'md5:2f7b5aa76edbc1a7a92cedcda8a528d5',
        }
    }
    _BASE_URL = 'http://animedigitalnetwork.fr'
    _RSA_KEY = (0xc35ae1e4356b65a73b551493da94b8cb443491c0aa092a357a5aee57ffc14dda85326f42d716e539a34542a0d3f363adf16c5ec222d713d5997194030ee2e4f0d1fb328c01a81cf6868c090d50de8e169c6b13d1675b9eeed1cbc51e1fffca9b38af07f37abd790924cd3bee59d0257cfda4fe5f3f0534877e21ce5821447d1b, 65537)
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
        webpage = self._download_webpage(url, video_id)
        player_config = self._parse_json(self._search_regex(
            r'playerConfig\s*=\s*({.+});', webpage,
            'player config', default='{}'), video_id, fatal=False)
        if not player_config:
            config_url = urljoin(self._BASE_URL, self._search_regex(
                r'(?:id="player"|class="[^"]*adn-player-container[^"]*")[^>]+data-url="([^"]+)"',
                webpage, 'config url'))
            player_config = self._download_json(
                config_url, video_id,
                'Downloading player config JSON metadata')['player']

        video_info = {}
        video_info_str = self._search_regex(
            r'videoInfo\s*=\s*({.+});', webpage,
            'video info', fatal=False)
        if video_info_str:
            video_info = self._parse_json(
                video_info_str, video_id, fatal=False) or {}

        options = player_config.get('options') or {}
        metas = options.get('metas') or {}
        links = player_config.get('links') or {}
        sub_path = player_config.get('subtitles')
        error = None
        if not links:
            links_url = player_config.get('linksurl') or options['videoUrl']
            token = options['token']
            self._K = ''.join([random.choice('0123456789abcdef') for _ in range(16)])
            message = bytes_to_intlist(json.dumps({
                'k': self._K,
                'e': 60,
                't': token,
            }))
            padded_message = intlist_to_bytes(pkcs1pad(message, 128))
            n, e = self._RSA_KEY
            encrypted_message = long_to_bytes(pow(bytes_to_long(padded_message), e, n))
            authorization = base64.b64encode(encrypted_message).decode()
            links_data = self._download_json(
                urljoin(self._BASE_URL, links_url), video_id,
                'Downloading links JSON metadata', headers={
                    'Authorization': 'Bearer ' + authorization,
                })
            links = links_data.get('links') or {}
            metas = metas or links_data.get('meta') or {}
            sub_path = sub_path or links_data.get('subtitles') or \
                'index.php?option=com_vodapi&task=subtitles.getJSON&format=json&id=' + video_id
            sub_path += '&token=' + token
            error = links_data.get('error')
        title = metas.get('title') or video_info['title']

        formats = []
        for format_id, qualities in links.items():
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
        if not error:
            error = options.get('error')
        if not formats and error:
            raise ExtractorError('%s said: %s' % (self.IE_NAME, error), expected=True)
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': strip_or_none(metas.get('summary') or video_info.get('resume')),
            'thumbnail': video_info.get('image'),
            'formats': formats,
            'subtitles': self.extract_subtitles(sub_path, video_id),
            'episode': metas.get('subtitle') or video_info.get('videoTitle'),
            'series': video_info.get('playlistTitle'),
        }
