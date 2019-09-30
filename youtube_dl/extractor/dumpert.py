# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    qualities,
    sanitized_Request,
)


class DumpertIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?dumpert\.nl/(?:mediabase|embed|item)/(?P<id>[0-9]+[/_][0-9a-zA-Z]+)'
    _TESTS = [{
        # This is an old-style URL. Note that the video ID consists of two
        # parts.
        'url': 'http://www.dumpert.nl/mediabase/6646981/951bc60f/',
        'md5': '1b9318d7d5054e7dcb9dc7654f21d643',
        'info_dict': {
            'id': '6646981_951bc60f',
            'ext': 'mp4',
            'title': 'Ik heb nieuws voor je',
            'description': 'Niet schrikken hoor',
            'thumbnail': r're:^https?://.*\.jpg$',
        }
    }, {
        # This is a new-style URL. Note that the two parts of the video ID are
        # now separated by _ instead of /.
        'url': 'https://www.dumpert.nl/item/6646981_951bc60f/',
        'md5': '1b9318d7d5054e7dcb9dc7654f21d643',
        'info_dict': {
            'id': '6646981_951bc60f',
            'ext': 'mp4',
            'title': 'Ik heb nieuws voor je',
            'description': 'Niet schrikken hoor',
            'thumbnail': r're:^https?://.*\.jpg$',
        }
    }, {
        'url': 'http://www.dumpert.nl/embed/6675421/dc440fe7/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id').replace('/', '_')

        url = 'https://www.dumpert.nl/item/%s' % (video_id)
        req = sanitized_Request(url)
        req.add_header('Cookie', 'filterNsfw=true; cpc=10')
        webpage = self._download_webpage(req, video_id)

        state = self._parse_json(self._parse_json(self._search_regex(
            r'__DUMPERT_STATE__\s*=\s*JSON\.parse\s*\(\s*(".+?")\s*\)\s*;',
            webpage, 'state'
        ), video_id), video_id)

        item = state.get('items', {}).get('item', {}).get('item')
        if not item:
            raise ExtractorError('Unable to find item on page')

        video = None
        for media_item in item.get('media', []):
            if media_item.get('mediatype') == 'VIDEO':
                video = media_item

        if not video:
            raise ExtractorError('Unable to find video on page')

        variants = video.get('variants', [])
        if not variants:
            raise ExtractorError('Unable to find video variants on page')

        quality = qualities(['flv', 'mobile', 'tablet', '720p'])

        formats = [{
            'url': variant.get('uri'),
            'format_id': variant.get('version'),
            'quality': quality(variant.get('version')),
        } for variant in variants if 'uri' in variant and 'version' in variant]
        self._sort_formats(formats)

        title = item.get('title') or self._og_search_title(webpage)
        description = item.get(
            'description') or self._og_search_description(webpage)
        thumbnail = item.get('still') or self._og_search_thumbnail(webpage)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'formats': formats
        }
