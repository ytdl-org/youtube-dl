# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    remove_end,
)


class TelegraafIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?telegraaf\.nl/tv/(?:[^/]+/)+(?P<id>\d+)/[^/]+\.html'
    _TEST = {
        'url': 'http://www.telegraaf.nl/tv/nieuws/binnenland/24353229/__Tikibad_ontruimd_wegens_brand__.html',
        'info_dict': {
            'id': '24353229',
            'ext': 'mp4',
            'title': 'Tikibad ontruimd wegens brand',
            'description': 'md5:05ca046ff47b931f9b04855015e163a4',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 33,
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        player_url = self._html_search_regex(
            r'<iframe[^>]+src="([^"]+")', webpage, 'player URL')
        player_page = self._download_webpage(
            player_url, video_id, note='Download player webpage')
        playlist_url = self._search_regex(
            r'playlist\s*:\s*"([^"]+)"', player_page, 'playlist URL')
        playlist_data = self._download_json(playlist_url, video_id)

        item = playlist_data['items'][0]
        formats = []
        locations = item['locations']
        for location in locations.get('adaptive', []):
            manifest_url = location['src']
            ext = determine_ext(manifest_url)
            if ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    manifest_url, video_id, ext='mp4', m3u8_id='hls', fatal=False))
            elif ext == 'mpd':
                formats.extend(self._extract_mpd_formats(
                    manifest_url, video_id, mpd_id='dash', fatal=False))
            else:
                self.report_warning('Unknown adaptive format %s' % ext)
        for location in locations.get('progressive', []):
            formats.append({
                'url': location['sources'][0]['src'],
                'width': location.get('width'),
                'height': location.get('height'),
                'format_id': 'http-%s' % location['label'],
            })

        self._sort_formats(formats)

        title = remove_end(self._og_search_title(webpage), ' - VIDEO')
        description = self._og_search_description(webpage)
        duration = item.get('duration')
        thumbnail = item.get('poster')

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'formats': formats,
            'duration': duration,
            'thumbnail': thumbnail,
        }
