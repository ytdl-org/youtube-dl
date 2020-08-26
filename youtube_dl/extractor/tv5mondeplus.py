# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    clean_html,
    determine_ext,
    extract_attributes,
    get_element_by_class,
    int_or_none,
    parse_duration,
    parse_iso8601,
)


class TV5MondePlusIE(InfoExtractor):
    IE_DESC = 'TV5MONDE+'
    _VALID_URL = r'https?://(?:www\.)?tv5mondeplus\.com/toutes-les-videos/[^/]+/(?P<id>[^/?#]+)'
    _TEST = {
        'url': 'http://www.tv5mondeplus.com/toutes-les-videos/documentaire/tdah-mon-amour-tele-quebec-tdah-mon-amour-ep001-enfants',
        'md5': '12130fc199f020673138a83466542ec6',
        'info_dict': {
            'id': 'tdah-mon-amour-tele-quebec-tdah-mon-amour-ep001-enfants',
            'ext': 'mp4',
            'title': 'Tdah, mon amour - Enfants',
            'description': 'md5:230e3aca23115afcf8006d1bece6df74',
            'upload_date': '20170401',
            'timestamp': 1491022860,
        }
    }
    _GEO_BYPASS = False

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        if ">Ce programme n'est malheureusement pas disponible pour votre zone géographique.<" in webpage:
            self.raise_geo_restricted(countries=['FR'])

        series = get_element_by_class('video-detail__title', webpage)
        title = episode = get_element_by_class(
            'video-detail__subtitle', webpage) or series
        if series and series != title:
            title = '%s - %s' % (series, title)
        vpl_data = extract_attributes(self._search_regex(
            r'(<[^>]+class="video_player_loader"[^>]+>)',
            webpage, 'video player loader'))

        video_files = self._parse_json(
            vpl_data['data-broadcast'], display_id).get('files', [])
        formats = []
        for video_file in video_files:
            v_url = video_file.get('url')
            if not v_url:
                continue
            video_format = video_file.get('format') or determine_ext(v_url)
            if video_format == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    v_url, display_id, 'mp4', 'm3u8_native',
                    m3u8_id='hls', fatal=False))
            else:
                formats.append({
                    'url': v_url,
                    'format_id': video_format,
                })
        self._sort_formats(formats)

        return {
            'id': display_id,
            'display_id': display_id,
            'title': title,
            'description': clean_html(get_element_by_class('video-detail__description', webpage)),
            'thumbnail': vpl_data.get('data-image'),
            'duration': int_or_none(vpl_data.get('data-duration')) or parse_duration(self._html_search_meta('duration', webpage)),
            'timestamp': parse_iso8601(self._html_search_meta('uploadDate', webpage)),
            'formats': formats,
            'episode': episode,
            'series': series,
        }
