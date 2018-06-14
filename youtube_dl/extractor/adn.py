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
    srt_subtitles_timecode,
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

    def _get_subtitles(self, sub_path, video_id):
        if not sub_path:
            return None

        enc_subtitles = self._download_webpage(
            urljoin(self._BASE_URL, sub_path),
            video_id, fatal=False)
        if not enc_subtitles:
            return None

        # http://animedigitalnetwork.fr/components/com_vodvideo/videojs/adn-vjs.min.js
        dec_subtitles = intlist_to_bytes(aes_cbc_decrypt(
            bytes_to_intlist(compat_b64decode(enc_subtitles[24:])),
            bytes_to_intlist(binascii.unhexlify(self._K + '9032ad7083106400')),
            bytes_to_intlist(compat_b64decode(enc_subtitles[:24]))
        ))
        subtitles_json = self._parse_json(
            dec_subtitles[:-compat_ord(dec_subtitles[-1])].decode(),
            None, fatal=False)
        if not subtitles_json:
            return None

        subtitles = {}
        for sub_lang, sub in subtitles_json.items():
            srt = ''
            for num, current in enumerate(sub):
                start, end, text = (
                    float_or_none(current.get('startTime')),
                    float_or_none(current.get('endTime')),
                    current.get('text'))
                if start is None or end is None or text is None:
                    continue
                srt += os.linesep.join(
                    (
                        '%d' % num,
                        '%s --> %s' % (
                            srt_subtitles_timecode(start),
                            srt_subtitles_timecode(end)),
                        text,
                        os.linesep,
                    ))

            if sub_lang == 'vostf':
                sub_lang = 'fr'
            subtitles.setdefault(sub_lang, []).extend([{
                'ext': 'json',
                'data': json.dumps(sub),
            }, {
                'ext': 'srt',
                'data': srt,
            }])
        return subtitles

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        player_config = self._parse_json(self._search_regex(
            r'playerConfig\s*=\s*({.+});', webpage, 'player config'), video_id)

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
                urljoin(self._BASE_URL, links_url), video_id, headers={
                    'Authorization': 'Bearer ' + authorization,
                })
            links = links_data.get('links') or {}
            metas = metas or links_data.get('meta') or {}
            sub_path = (sub_path or links_data.get('subtitles')) + '&token=' + token
            error = links_data.get('error')
        title = metas.get('title') or video_info['title']

        formats = []
        for format_id, qualities in links.items():
            if not isinstance(qualities, dict):
                continue
            for load_balancer_url in qualities.values():
                load_balancer_data = self._download_json(
                    load_balancer_url, video_id, fatal=False) or {}
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
