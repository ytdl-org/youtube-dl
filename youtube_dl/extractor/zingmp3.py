# coding=utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import ExtractorError


class ZingMp3BaseInfoExtractor(InfoExtractor):

    def _extract_item(self, item):
        error_message = item.find('./errormessage').text
        if error_message:
            raise ExtractorError(
                '%s returned error: %s' % (self.IE_NAME, error_message),
                expected=True)

        title = item.find('./title').text.strip()
        source = item.find('./source').text
        extension = item.attrib['type']
        thumbnail = item.find('./backimage').text

        return {
            'title': title,
            'url': source,
            'ext': extension,
            'thumbnail': thumbnail,
        }

    def _extract_player_xml(self, player_xml_url, id, playlist_title=None):
        player_xml = self._download_xml(player_xml_url, id, 'Downloading Player XML')
        items = player_xml.findall('./item')

        if len(items) == 1:
            # one single song
            data = self._extract_item(items[0])
            data['id'] = id

            return data
        else:
            # playlist of songs
            entries = []

            for i, item in enumerate(items, 1):
                entry = self._extract_item(item)
                entry['id'] = '%s-%d' % (id, i)
                entries.append(entry)

            return {
                '_type': 'playlist',
                'id': id,
                'title': playlist_title,
                'entries': entries,
            }


class ZingMp3SongIE(ZingMp3BaseInfoExtractor):
    _VALID_URL = r'https?://mp3\.zing\.vn/bai-hat/(?P<slug>[^/]+)/(?P<song_id>\w+)\.html'
    _TESTS = [{
        'url': 'http://mp3.zing.vn/bai-hat/Xa-Mai-Xa-Bao-Thy/ZWZB9WAB.html',
        'md5': 'ead7ae13693b3205cbc89536a077daed',
        'info_dict': {
            'id': 'ZWZB9WAB',
            'title': 'Xa Mãi Xa',
            'ext': 'mp3',
            'thumbnail': 're:^https?://.*\.jpg$',
        },
    }]
    IE_NAME = 'zingmp3:song'
    IE_DESC = 'mp3.zing.vn songs'

    def _real_extract(self, url):
        matched = re.match(self._VALID_URL, url)
        slug = matched.group('slug')
        song_id = matched.group('song_id')

        webpage = self._download_webpage(
            'http://mp3.zing.vn/bai-hat/%s/%s.html' % (slug, song_id), song_id)

        player_xml_url = self._search_regex(
            r'&amp;xmlURL=(?P<xml_url>[^&]+)&', webpage, 'player xml url')

        return self._extract_player_xml(player_xml_url, song_id)


class ZingMp3AlbumIE(ZingMp3BaseInfoExtractor):
    _VALID_URL = r'https?://mp3\.zing\.vn/album/(?P<slug>[^/]+)/(?P<album_id>\w+)\.html'
    _TESTS = [{
        'url': 'http://mp3.zing.vn/album/Lau-Dai-Tinh-Ai-Bang-Kieu-Minh-Tuyet/ZWZBWDAF.html',
        'info_dict': {
            '_type': 'playlist',
            'id': 'ZWZBWDAF',
            'title': 'Lâu Đài Tình Ái - Bằng Kiều ft. Minh Tuyết | Album 320 lossless',
        },
        'playlist_count': 10,
    }]
    IE_NAME = 'zingmp3:album'
    IE_DESC = 'mp3.zing.vn albums'

    def _real_extract(self, url):
        matched = re.match(self._VALID_URL, url)
        slug = matched.group('slug')
        album_id = matched.group('album_id')

        webpage = self._download_webpage(
            'http://mp3.zing.vn/album/%s/%s.html' % (slug, album_id), album_id)
        player_xml_url = self._search_regex(
            r'&amp;xmlURL=(?P<xml_url>[^&]+)&', webpage, 'player xml url')

        return self._extract_player_xml(
            player_xml_url, album_id,
            playlist_title=self._og_search_title(webpage))
