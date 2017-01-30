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
    _VALID_URL = r'visir:(?P<id>[^:]+):(?P<type>(?:audio|video)):(?P<category>\d+):(?P<subcategory>\d+)'
    _BASE_URL = 'http://www.visir.is'

    def _extract_player_info(self, video_id, webpage, default=NO_DEFAULT):
        field_names = ('FileId', 'Categoryid', 'Subcategoryid', 'Type', 'File')
        player_info_regex = r'App\.Player\.Init\s*\(\s*(.+?)\)'
        player_info_script = self._search_regex(
            player_info_regex, webpage, 'player info', default=default)
        if not player_info_script:
            return len(field_names) * [None]
        player_info_dict = self._parse_json(
            player_info_script, video_id, transform_source=js_to_json)
        return (player_info_dict.get(name) for name in field_names)

    def _extract_fields_from_media_list(self, video_id, category, subcategory, media_type):
        url = 'http://www.visir.is/section/MEDIA?template=related_json&kat=%s&subkat=%s' % (category, subcategory)
        if media_type == 'audio':
            url += '&type=audio'
        media_collection = self._download_json(url, video_id)
        field_names = ('link', 'file', 'title', 'image')
        return next(
            (e.get(field) for field in field_names) for e in media_collection if e.get('mediaid') == video_id)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id, media_type, category_id, subcategory_id = mobj.group(
            'id', 'type', 'category', 'subcategory')
        media_link, _, _, _ = self._extract_fields_from_media_list(
            video_id, category_id, subcategory_id, media_type)
        return self.url_result(
            urljoin(self._BASE_URL, media_link), ie=VisirMediaIE.ie_key())


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

    def _extract_formats(self, video_id, playlist_url, filepath):
        formats = self._extract_wowza_formats(
            playlist_url, video_id, skip_protocols=['dash'])
        formats.append(
            {'url': urljoin('http://static.visir.is/', filepath)})
        self._sort_formats(formats)
        return formats

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        description = self._og_search_description(webpage, default=None)

        _, category_id, subcategory_id, media_type, filepath = self._extract_player_info(
            video_id, webpage)

        _, playlist_url, title, thumbnail = self._extract_fields_from_media_list(
            video_id, category_id, subcategory_id, media_type)

        formats = self._extract_formats(
            video_id, playlist_url, filepath)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'formats': formats,
        }

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
        video_id, category_id, subcategory_id, media_type, _= self._extract_player_info(
            article_id, webpage, default=None) # TODO: default?
        if video_id and category_id and subcategory_id and media_type in ('video', 'audio'):
            entries.append(self.url_result(
                'visir:%s:%s:%s:%s' % (video_id, media_type, category_id, subcategory_id),
                ie=VisirBaseIE.ie_key()))

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
