# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    qualities,
    int_or_none,
    mimetype2ext,
    determine_ext,
)


class SixPlayIE(InfoExtractor):
    _VALID_URL = r'(?:6play:|https?://(?:www\.)?6play\.fr/.+?-c_)(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.6play.fr/jamel-et-ses-amis-au-marrakech-du-rire-p_1316/jamel-et-ses-amis-au-marrakech-du-rire-2015-c_11495320',
        'md5': '42310bffe4ba3982db112b9cd3467328',
        'info_dict': {
            'id': '11495320',
            'ext': 'mp4',
            'title': 'Jamel et ses amis au Marrakech du rire 2015',
            'description': 'md5:ba2149d5c321d5201b78070ee839d872',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        clip_data = self._download_json(
            'https://player.m6web.fr/v2/video/config/6play-auth/FR/%s.json' % video_id,
            video_id)
        video_data = clip_data['videoInfo']

        quality_key = qualities(['lq', 'sd', 'hq', 'hd'])
        formats = []
        for source in clip_data['sources']:
            source_type, source_url = source.get('type'), source.get('src')
            if not source_url or source_type == 'hls/primetime':
                continue
            ext = mimetype2ext(source_type) or determine_ext(source_url)
            if ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    source_url, video_id, 'mp4', 'm3u8_native',
                    m3u8_id='hls', fatal=False))
                formats.extend(self._extract_f4m_formats(
                    source_url.replace('.m3u8', '.f4m'),
                    video_id, f4m_id='hds', fatal=False))
            elif ext == 'mp4':
                quality = source.get('quality')
                formats.append({
                    'url': source_url,
                    'format_id': quality,
                    'quality': quality_key(quality),
                    'ext': ext,
                })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': video_data['title'].strip(),
            'description': video_data.get('description'),
            'duration': int_or_none(video_data.get('duration')),
            'series': video_data.get('titlePgm'),
            'formats': formats,
        }
