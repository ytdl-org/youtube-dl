# coding: utf-8
from __future__ import unicode_literals

import json
import os

from .common import InfoExtractor
from ..aes import aes_cbc_decrypt
from ..compat import (
    compat_b64decode,
    compat_ord,
)
from ..utils import (
    ass_subtitles_timecode,
    bytes_to_intlist,
    ExtractorError,
    float_or_none,
    intlist_to_bytes,
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

    def _get_subtitles(self, sub_path, video_id):
        if not sub_path:
            return None

        enc_subtitles = self._download_webpage(
            urljoin(self._BASE_URL, sub_path),
            video_id, fatal=False, headers={
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:53.0) Gecko/20100101 Firefox/53.0',
            })
        if not enc_subtitles:
            return None

        # http://animedigitalnetwork.fr/components/com_vodvideo/videojs/adn-vjs.min.js
        dec_subtitles = intlist_to_bytes(aes_cbc_decrypt(
            bytes_to_intlist(compat_b64decode(enc_subtitles[24:])),
            bytes_to_intlist(b'\x09\x36\x8b\x97\xe7\xcc\x6c\x31\x1b\xad\x31\x24\xd3\x79\xc8\xd4'),
            bytes_to_intlist(compat_b64decode(enc_subtitles[:24]))
        ))
        subtitles_json = self._parse_json(
            dec_subtitles[:-compat_ord(dec_subtitles[-1])].decode(),
            None, fatal=False)
        if not subtitles_json:
            return None

        ass = os.linesep.join(
            (
                '[Script Info]',
                'ScriptType: v4.00+',
                'WrapStyle: 0',
                os.linesep,
                '[Aegisub Project Garbage]',
                'Last Style Storage: Default',
                os.linesep,
                '[V4+ Styles]',
                'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding',
                'Style: Default,Verdana,16,&H00FFFFFF,&H000000FF,&H00000000,&HAA000000,-1,0,0,0,100,100,0,0,1,0.8,0.5,2,20,20,20,1',
                'Style: ST_BAS_GAUCHE,Verdana,16,&H00FFFFFF,&H000000FF,&H00000000,&HAA000000,-1,0,0,0,100,100,0,0,1,0.8,0.5,1,41,20,30,1',
                'Style: ST_BAS_DROITE,Verdana,16,&H00FFFFFF,&H000000FF,&H00000000,&HAA000000,-1,0,0,0,100,100,0,0,1,0.8,0.5,3,20,41,30,1',
                'Style: ST_HAUT,Verdana,16,&H00FFFFFF,&H000000FF,&H00000000,&HAA000000,-1,0,0,0,100,100,0,0,1,0.8,0.5,8,20,20,30,1',
                'Style: ST_HAUT_GAUCHE,Verdana,16,&H00FFFFFF,&H000000FF,&H00000000,&HAA000000,-1,0,0,0,100,100,0,0,1,0.8,0.5,7,41,20,30,1',
                'Style: ST_HAUT_ALT,Verdana,16,&H00FFFFFF,&H000000FF,&H00000000,&HAA000000,-1,0,0,0,100,100,0,0,1,0.8,0.5,2,20,20,40,1',
                'Style: ST_HAUT_DROITE,Verdana,16,&H00FFFFFF,&H000000FF,&H00000000,&HAA000000,-1,0,0,0,100,100,0,0,1,0.8,0.5,9,20,41,30,1',
                os.linesep,
                '[Events]',
                'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text',
                '',
            )
        )
        subtitles = {}
        for sub_lang, sub in subtitles_json.items():
            srt = ''
            for num, current in enumerate(sub):
                start, end, text, lineAlign, positionAlign = (
                    float_or_none(current.get('startTime')),
                    float_or_none(current.get('endTime')),
                    current.get('text'),
                    current.get('lineAlign'),
                    current.get('positionAlign'))
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

                if (lineAlign == 'start' and positionAlign == 'middle'):
                    position = 'Default'
                elif (lineAlign == 'end' and positionAlign == 'middle'):
                    position = 'ST_HAUT'
                elif (lineAlign == 'end' and positionAlign == 'start'):
                    position = 'ST_HAUT_GAUCHE'
                elif (lineAlign == 'end' and positionAlign == 'end'):
                    position = 'ST_HAUT_DROITE'
                elif (lineAlign == 'start' and positionAlign == 'start'):
                    position = 'ST_BAS_GAUCHE'
                elif (lineAlign == 'start' and positionAlign == 'end'):
                    position = 'ST_BAS_DROITE'
                elif (lineAlign == 'middle' and positionAlign == 'middle'):
                    position = 'ST_HAUT_ALT'
                else:
                    position = 'Default'

                ass += os.linesep.join(
                    (
                        'Dialogue: 0,%s,%s,%s,,0,0,0,,%s' % (
                            ass_subtitles_timecode(start),
                            ass_subtitles_timecode(end),
                            position,
                            text.replace("\n", "\\N").replace("<i>", "{\\i1}").replace("</i>", "{\\i0}")
                        ),
                        '',
                    ))

            if sub_lang == 'vostf':
                sub_lang = 'fr'
            subtitles.setdefault(sub_lang, []).extend([{
                'ext': 'json',
                'data': json.dumps(sub),
            }, {
                'ext': 'srt',
                'data': srt,
            }, {
                'ext': 'ass',
                'data': ass,
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
            links_data = self._download_json(urljoin(
                self._BASE_URL, links_url), video_id)
            links = links_data.get('links') or {}
            metas = metas or links_data.get('meta') or {}
            sub_path = sub_path or links_data.get('subtitles')
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
