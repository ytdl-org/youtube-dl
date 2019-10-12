# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

from ..utils import (
    ExtractorError,
    urljoin,
    parse_duration,
)


class MakoTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?mako\.co\.il/.+?/(?:VOD|Video)-(?P<id>[0-9a-f]{18})\.htm'
    _TESTS = [
        {
            'url': 'https://www.mako.co.il/mako-vod-keshet/parliament-s1/VOD-5df5a86c1966831006.htm',
            'md5': 'd826489500d23d122055a30df0d59cb5',
            'info_dict': {
                'id': '5df5a86c1966831006',
                'ext': 'm3u8',
                'title': '\u05d4\u05e4\u05e8\u05dc\u05de\u05e0\u05d8 | \u05e4\u05e8\u05e7 1 \u05dc\u05e6\u05e4\u05d9\u05d9\u05d4 \u05d9\u05e9\u05d9\u05e8\u05d4 | makoTV ',
                'thumbnail': r're:^https?://img\.mako\.co\.il/\d{4}/\d{2}/\d{2}/.+\.jpg$',
                'description': '\u05e9\u05d0\u05d5\u05dc\u05d9, \u05d0\u05de\u05e6\u05d9\u05d4, \u05d4\u05e7\u05d8\u05d5\u05e8, \u05e7\u05e8\u05e7\u05d5 \u05d5\u05d0\u05d1\u05d9 \u05de\u05e7\u05d1\u05dc\u05d9\u05dd \u05e1\u05d3\u05e8\u05d4 \u05de\u05e9\u05dc\u05d4\u05dd. \u05db\u05dc \u05d4\u05e4\u05e8\u05e7\u05d9\u05dd \u05e9\u05dc \u05d4\u05e4\u05e8\u05dc\u05de\u05e0\u05d8 \u05dc\u05e6\u05e4\u05d9\u05d9\u05d4 \u05d9\u05e9\u05d9\u05e8\u05d4 | makoTV ',
                'upload_date': '20120708',
                'timestamp': 1341751140,
                'duration': 1774.0,
                'episode_number': 1,
                'episode': '\u05e4\u05e8\u05e7 1',
                'season': '\u05e2\u05d5\u05e0\u05d4 1',
            },
        },
        {
            'url': 'https://www.mako.co.il/tv-erez-nehederet/season14-shauli-and-irena/Video-6c53a12777d9c51006.htm',
            'md5': '77b0c836ebfb6237c7e9b909e57a4194',
            'info_dict': {
                'id': '6c53a12777d9c51006',
                'ext': 'm3u8',
                'title': '\u05e9\u05d0\u05d5\u05dc\u05d9 \u05d5\u05d0\u05d9\u05e8\u05e0\u05d4 \u05d1\u05d1\u05d9\u05ea \u05d7\u05d5\u05dc\u05d9\u05dd \u2013 \u05e4\u05e8\u05e7 \u05d4\u05e1\u05d9\u05d5\u05dd',
                'thumbnail': r're:^https?://img\.mako\.co\.il/\d{4}/\d{2}/\d{2}/.+\.jpg$',
                'description': '\u05d4\u05d0\u05dd \u05e9\u05d0\u05d5\u05dc\u05d9 \u05d4\u05d5\u05dc\u05da \u05dc\u05de\u05d5\u05ea?',
                'duration': 669.0,
                'episode': '\u05e9\u05d0\u05d5\u05dc\u05d9 \u05d5\u05d0\u05d9\u05e8\u05e0\u05d4 \u05d1\u05d1\u05d9\u05ea \u05d7\u05d5\u05dc\u05d9\u05dd \u2013 \u05e4\u05e8\u05e7 \u05d4\u05e1\u05d9\u05d5\u05dd',
            },
        },
    ]


    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        vcmid_pattern = r'var vcmidOfContent\s*?=\s*?\'([0-9A-Za-z]{40})\''
        vcmid = self._search_regex(vcmid_pattern, webpage, 'vcmid')
        channel_id_pattern = r'var currentChannelId\s*?=\s*?\'([0-9A-Za-z]{40})\''
        channel_id = self._search_regex(channel_id_pattern, webpage, 'channel_id')

        config_new_url = 'https://rcs.mako.co.il/flash_swf/players/makoPlayer/configNew.xml'
        config_new = self._download_xml(config_new_url, video_id)
        playlist_url = config_new.findtext('./PlaylistUrl')
        playlist_url = playlist_url.replace('$$vcmid$$', vcmid)
        playlist_url = playlist_url.replace('$$videoChannelId$$', channel_id)
        playlist_url = playlist_url.replace('$$galleryChannelId$$', vcmid)
        playlist_url = urljoin('https://www.mako.co.il', playlist_url)
        playlist = self._download_json(playlist_url, video_id)

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
                ticket_url = urljoin('https://makostore-hd.ctedgecdn.net', ticket['url']) + '?' + ticket['ticket']
                formats.extend(self._extract_m3u8_formats(ticket_url, video_id, fatal=False))

        self._sort_formats(formats)

        info = {
            'id': video_id,
            'formats': formats,
        }

        try:
            json_ld = self._search_json_ld(webpage, video_id, fatal=False)
        except ExtractorError:
            json_ld = None
        if json_ld is not None:
            info.update(json_ld)

        info.update({
            'url': self._og_search_url(webpage),
            'title': self._og_search_title(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'description': self._og_search_description(webpage),
        })

        video_details = playlist['videoDetails']
        info.update({
            'url': video_details['directLink'],
            'duration': parse_duration(video_details['duration']),
            'view_count': video_details['numViews'],
            'average_rating': video_details['rank'],
            'episode': video_details['title'],
            'season': video_details['season'],
        })
        try:
            info.update({'episode_number': int(video_details['episodeNumber'])})
        except ValueError:
            pass

        return info
