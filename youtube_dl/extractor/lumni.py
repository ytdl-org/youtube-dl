# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .francetv import FranceTVIE
from ..utils import orderedSet


class LumniIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?lumni\.fr/video/(?P<id>[0-9a-z-]+)'
    _TEST = {
        'url': 'https://www.lumni.fr/video/la-guerre-froide',
        'md5': '31158a5b300083ba373f4fc85dd88272',
        'info_dict': {
            'id': '302dbf40-b0df-4847-926b-99fdf4f10162',
            'ext': 'mp4',
            'timestamp': 1585754978,
            'upload_date': '20200401',
            'title': 'La guerre froide (1er avril)',
        }
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        video_id = self._search_regex(
            r'data-factoryid="([^"]+)',
            webpage, 'video id')
        full_id = 'francetv:%s' % video_id

        return self.url_result(full_id,
                               ie=FranceTVIE.ie_key(),
                               video_id=video_id)


class LumniPlaylistIE(InfoExtractor):
    _VALID_URL = r'''https?://
                        (?:www\.)?lumni\.fr/
                        (?:dossier|programme|serie)/
                        (?P<id>[0-9a-z-]+)
                    '''
    _TESTS = [{
        'url': 'https://www.lumni.fr/dossier/les-fondamentaux-vocabulaire',
        'info_dict': {
            'id': 'les-fondamentaux-vocabulaire',
            'title': 'Les Fondamentaux : Vocabulaire',
        },
        'playlist_mincount': 39
    }, {
        'url': 'https://www.lumni.fr/programme/the-rich-morning-show',
        'only_matching': True
    }, {
        'url': 'https://www.lumni.fr/serie/la-maison-lumni-college',
        'only_matching': True
    }
    ]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)

        webpage = self._download_webpage(url, playlist_id)

        entries = [self.url_result(
            'https://lumni.fr/video/%s' % video_id,
            ie=LumniIE.ie_key(), video_id=video_id)
            for video_id in orderedSet(re.findall(
                r'<a[^>]+\bhref=["\']/video/([0-9a-z-]+)', webpage))]

        playlist_title = self._og_search_title(webpage)

        return self.playlist_result(entries, playlist_id, playlist_title)
