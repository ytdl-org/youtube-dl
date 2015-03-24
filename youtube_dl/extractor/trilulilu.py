# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import ExtractorError


class TriluliluIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?trilulilu\.ro/(?:video-[^/]+/)?(?P<id>[^/#\?]+)'
    _TEST = {
        'url': 'http://www.trilulilu.ro/video-animatie/big-buck-bunny-1',
        'md5': 'c1450a00da251e2769b74b9005601cac',
        'info_dict': {
            'id': 'ae2899e124140b',
            'ext': 'mp4',
            'title': 'Big Buck Bunny',
            'description': ':) pentru copilul din noi',
        },
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        if re.search(r'Fişierul nu este disponibil pentru vizionare în ţara dumneavoastră', webpage):
            raise ExtractorError(
                'This video is not available in your country.', expected=True)
        elif re.search('Fişierul poate fi accesat doar de către prietenii lui', webpage):
            raise ExtractorError('This video is private.', expected=True)

        flashvars_str = self._search_regex(
            r'block_flash_vars\s*=\s*(\{[^\}]+\})', webpage, 'flashvars', fatal=False, default=None)

        if flashvars_str:
            flashvars = self._parse_json(flashvars_str, display_id)
        else:
            raise ExtractorError(
                'This page does not contain videos', expected=True)

        if flashvars['isMP3'] == 'true':
            raise ExtractorError(
                'Audio downloads are currently not supported', expected=True)

        video_id = flashvars['hash']
        title = self._og_search_title(webpage)
        thumbnail = self._og_search_thumbnail(webpage)
        description = self._og_search_description(webpage, default=None)

        format_url = ('http://fs%(server)s.trilulilu.ro/%(hash)s/'
                      'video-formats2' % flashvars)
        format_doc = self._download_xml(
            format_url, video_id,
            note='Downloading formats',
            errnote='Error while downloading formats')

        video_url_template = (
            'http://fs%(server)s.trilulilu.ro/stream.php?type=video'
            '&source=site&hash=%(hash)s&username=%(userid)s&'
            'key=ministhebest&format=%%s&sig=&exp=' %
            flashvars)
        formats = [
            {
                'format_id': fnode.text.partition('-')[2],
                'url': video_url_template % fnode.text,
                'ext': fnode.text.partition('-')[0]
            }

            for fnode in format_doc.findall('./formats/format')
        ]

        return {
            'id': video_id,
            'display_id': display_id,
            'formats': formats,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
        }
