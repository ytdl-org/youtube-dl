# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

from ..utils import (
    update_url_query,
    urljoin,
)


class MakoTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?mako\.co\.il/mako-vod-.+/VOD-(?P<id>[0-9a-f]{18})\.htm'
    _TEST = {
        'url': 'https://www.mako.co.il/mako-vod-keshet/parliament-s1/VOD-5df5a86c1966831006.htm',
        'md5': 'd826489500d23d122055a30df0d59cb5',
        'info_dict': {
            'id': '5df5a86c1966831006',
            'ext': 'm3u8',
            'title': 'הפרלמנט | פרק 1 לצפייה ישירה | makoTV ',
            'thumbnail': r're:^https?://img\.mako\.co\.il/\d{4}/\d{2}/\d{2}/.*\.jpg$',
            'description': 'שאולי, אמציה, הקטור, קרקו ואבי מקבלים סדרה משלהם. כל הפרקים של הפרלמנט לצפייה ישירה | makoTV ',
            'upload_date': '20120708',
            'timestamp': 1341751140
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        service_query = {'type': 'service'}
        service = self._download_json(update_url_query(url, service_query), video_id)
        video = service['root']['video']

        config_new = self._download_xml('https://rcs.mako.co.il/flash_swf/players/makoPlayer/configNew.xml', video_id)
        playlist_url = config_new.findtext('./PlaylistUrl')
        playlist_url = playlist_url.replace('$$vcmid$$', video['guid'])
        playlist_url = playlist_url.replace('$$videoChannelId$$', video['chId'])
        playlist_url = playlist_url.replace('$$galleryChannelId$$', video['galleryChId'])
        playlist = self._download_json(urljoin('https://www.mako.co.il', playlist_url), video_id)

        formats = []
        for media in playlist.get('media', []):
            tickets_url = 'https://mass.mako.co.il/ClicksStatistics/entitlementsServicesV2.jsp'
            tickets_query = {
                'et': 'gt',
                'lp': media['url'],
                'rv': media['cdn'],
            }
            tickets = self._download_json(tickets_url, video_id, query=tickets_query, fatal=False)
            if tickets is None or tickets.get('status', '').lower() != 'success':
                continue
            for ticket in tickets.get('tickets', {}):
                ticket_url = urljoin('https://makostore-hd.ctedgecdn.net', ticket['url']) + "?" + ticket['ticket']
                formats.extend(self._extract_m3u8_formats(ticket_url, video_id, fatal=False))

        self._sort_formats(formats)

        info = self._search_json_ld(webpage, video_id, fatal=False)
        if info is None:
            info = {}
        info.update({
            'id': video_id,
            'title': self._og_search_title(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'description': self._og_search_description(webpage),
            'formats': formats,
        })

        return info
