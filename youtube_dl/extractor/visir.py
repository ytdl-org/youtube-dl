# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    NO_DEFAULT,
    js_to_json,
    remove_start,
    urljoin,
)


class VisirBaseIE(InfoExtractor):
    _URL_BASE = 'http://www.visir.is'

    def _extract_player_info_dict(self, webpage, display_id, default=NO_DEFAULT):
        player_info_regex = r'App\.Player\.Init\s*\(\s*(.+?)\)'
        player_info_script = self._search_regex(
            player_info_regex, webpage, 'player info', default=default)
        if player_info_script:
            return self._parse_json(
                player_info_script, display_id, transform_source=js_to_json)
        return default

    def _extract_playlist_dict(self, media_id, category_id, subcategory_id, media_type):
        url = urljoin(
            self._URL_BASE, '/section/MEDIA?template=related_json&kat=%s&subkat=%s' % (category_id, subcategory_id))
        if media_type == 'audio':
            url += '&type=audio'
        media_collection = self._download_json(url, media_id)
        return next(
            media_entry for media_entry in media_collection if media_entry.get('mediaid') == media_id)

    def _extract_formats(self, media_id, playlist_url, filepath):
        formats = []
        if playlist_url:
            formats = self._extract_wowza_formats(
                playlist_url, media_id, skip_protocols=['dash', 'rtmp', 'rtsp'])
        formats.append(
            {'url': urljoin('http://static.visir.is/', filepath)})
        self._sort_formats(formats)
        return formats

    def _extract_media(self, player_info_dict, media_id, description=None):
        category_id = player_info_dict.get('Categoryid')
        subcategory_id = player_info_dict.get('Subcategoryid')
        media_type = player_info_dict.get('Type')
        filepath = player_info_dict.get('File')

        try:
            playlist_dict = self._extract_playlist_dict(media_id, category_id, subcategory_id, media_type)
            title = playlist_dict.get('title')
            thumbnail = playlist_dict.get('image')
            playlist_url = playlist_dict.get('file')

        except StopIteration:
            # Fallback if video is not found in playlist_dict:
            title = player_info_dict.get('Title')
            thumbnail = player_info_dict.get('image')
            if media_type == 'video':
                geoblock = player_info_dict.get('GeoBlock')
                host = player_info_dict.get('Host')
                geo = '-geo/' if geoblock else '/'
                playlist_url = 'http://' + host + '/hls-vod' + geo + '_definst_/mp4:' + filepath + '/playlist.m3u8'
            else:
                playlist_url = None

        formats = self._extract_formats(media_id, playlist_url, filepath)

        return {
            'id': media_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'formats': formats,
        }


class VisirMediaIE(VisirBaseIE):
    _VALID_URL = r'https?://(?:www\.)?visir\.is/section(?:/media)?/.+?fileid=(?P<id>[^/]+)$'
    _TESTS = [{
        'url': 'http://www.visir.is/section/MEDIA99&fileid=CLP51729',
        'md5': '1486324696d1b9f30fcea985a7922f2c',
        'info_dict': {
            'id': 'CLP51729',
            'ext': 'mp4',
            'title': u'Guðjón: Mjög jákvæður á framhaldið',
            'description': None,
            'thumbnail': 'http://www.visir.is/apps/pbcsi.dll/urlget?url=/ExternalData/IsBolti_clips/51729_3.jpg'
        },
    }, {
        'url': 'http://www.visir.is/section/MEDIA98&fileid=CLP49923',
        'info_dict': {
            'id': 'CLP49923',
            'ext': 'mp3',
            'title': u'Ósk Gunnars - Sigga Soffía og dansverkið FUBAR',
            'description': u'Ósk Gunnars alla virka daga á FM957 frá 13-17',
        },
        'params': {
            'skip_download': True,
        },
    }]

    def _real_extract(self, url):
        media_id = self._match_id(url)
        webpage = self._download_webpage(url, media_id)

        player_info_dict = self._extract_player_info_dict(webpage, media_id)

        description = self._og_search_description(webpage, default=None)
        return self._extract_media(player_info_dict, media_id, description=description)


class VisirArticleIE(VisirBaseIE):
    _VALID_URL = r'https?://(?:www\.)?visir\.is/.+/article/(?P<id>\d+)$'
    _TEST = {
        'url': 'http://www.visir.is/landsmenn-minntust-birnu-brjansdottur/article/2017170128825',
        'info_dict': {
            'id': '2017170128825',
            'title': u'Landsmenn minntust Birnu Brjánsdóttur',
            'description': u'Hundruð kerta voru tendruð á Arnarhóli í ljósaskiptunum í dag.'
        },
        'playlist_count': 2,
    }

    def _real_extract(self, url):
        article_id = self._match_id(url)
        webpage = self._download_webpage(url, article_id)

        title = remove_start(self._og_search_title(webpage), u'Vísir -').strip()
        description = self._og_search_description(webpage, default=None)

        entries = []

        # Try to find the main video of the article:
        player_info_dict = self._extract_player_info_dict(webpage, article_id, default=None)
        if player_info_dict:
            media_id = player_info_dict.get('FileId')
            entries.append(self._extract_media(player_info_dict, media_id))

        # Try to find embedded visir videos:
        video_urls = [m.group('url') for m in re.finditer(
            r'<iframe[^>]+src=(["\'])(?P<url>http://www\.visir\.is/section/.+?)\1', webpage)]
        for url in video_urls:
            entries.append(self.url_result(url, ie=VisirMediaIE.ie_key()))

        return self.playlist_result(
            entries,
            playlist_id=article_id,
            playlist_title=title,
            playlist_description=description)
