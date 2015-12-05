# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    parse_iso8601,
    js_to_json,
    parse_duration,
)


class TriluliluIE(InfoExtractor):
    _VALID_URL = r'https?://(?:(?:www|m)\.)?trilulilu\.ro/(?:[^/]+/)?(?P<id>[^/#\?]+)'
    _TESTS = [{
        'url': 'http://www.trilulilu.ro/big-buck-bunny-1',
        'md5': '68da087b676a6196a413549212f60cc6',
        'info_dict': {
            'id': 'ae2899e124140b',
            'ext': 'mp4',
            'title': 'Big Buck Bunny',
            'description': ':) pentru copilul din noi',
            'uploader_id': 'chipy',
            'upload_date': '20120304',
            'timestamp': 1330830647,
        },
    }, {
        'url': 'http://www.trilulilu.ro/adena-ft-morreti-inocenta',
        'md5': '929dfb8729dc71750463af88bbbbf4a4',
        'info_dict': {
            'id': 'f299710e3c91c5',
            'ext': 'mp4',
            'title': 'Adena ft. Morreti - Inocenta',
            'description': 'pop music',
            'uploader_id': 'VEVOmixt',
            'upload_date': '20151204',
            'timestamp': 1449187937,
        },
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        if re.search(r'Fişierul nu este disponibil pentru vizionare în ţara dumneavoastră', webpage):
            raise ExtractorError(
                'This video is not available in your country.', expected=True)
        elif re.search('Fişierul poate fi accesat doar de către prietenii lui', webpage):
            raise ExtractorError('This video is private.', expected=True)

        player_vars = self._parse_json(
            self._search_regex(r'(?s)playerVars\s*=\s*({.+?});', webpage, 'player vars'),
            display_id, js_to_json)

        uploader_id, media_id = self._search_regex(
            r'<input type="hidden" id="identifier" value="([^"]+)"',
            webpage, 'identifier').split('|')

        media_class = player_vars.get('fileClass')
        if media_class not in ('video', 'audio'):
            raise ExtractorError('not a video or an audio')

        # TODO: get correct ext for audio files
        formats = [{
            'url': player_vars['file'],
            'ext': player_vars.get('streamType'),
        }]

        hd_url = player_vars.get('fileUrlHD')
        if hd_url:
            formats.append({
                'format_id': 'hd',
                'url': hd_url,
                'ext': player_vars.get('fileTypeHD'),
            })

        if media_class == 'audio':
            formats[0]['vcodec'] = 'none'
        else:
            formats[0]['format_id'] = 'sd'

        return {
            'id': media_id,
            'display_id': display_id,
            'formats': formats,
            'title': self._og_search_title(webpage),
            'description': self._og_search_description(webpage),
            'thumbnail': player_vars.get('image'),
            'uploader_id': uploader_id,
            'timestamp': parse_iso8601(self._html_search_meta('uploadDate', webpage), ' '),
            'duration': parse_duration(self._html_search_meta('duration', webpage)),
        }
