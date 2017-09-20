# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    smuggle_url,
    js_to_json,
)


class CNBCIE(InfoExtractor):
    _VALID_URL = r'https?://www\.cnbc\.com/video/[0-9]{4}/[0-9]{2}/[0-9]{2}/(?P<title>.+)\.html'
    _TEST = {
        'url': 'https://www.cnbc.com/video/2016/03/30/fighting-zombies-is-big-business.html',
        'info_dict': {
            'id': '3000503714',
            'ext': 'mp4',
            'title': 'Fighting zombies is big business',
            'description': 'md5:0c100d8e1a7947bd2feec9a5550e519e',
            'timestamp': 1459332000,
            'upload_date': '20160330',
            'uploader': 'NBCU-CNBC',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        mob = re.search(self._VALID_URL, url)
        video_id = mob.group('title')
        webpage = self._download_webpage(url, video_id)
        mobj = re.search(
                r'mpscall\s*=\s*(?P<json_data>[^)]+),\s*mpsopts',
            webpage)
        if mobj is None:
            raise ExtractorError('Unable to extract video urls')

        urls_info = self._parse_json(
            mobj.group('json_data'), video_id, transform_source = js_to_json)

        return {
            '_type': 'url_transparent',
            'ie_key': 'ThePlatform',
            'url': smuggle_url(
                'http://link.theplatform.com/s/gZWlPC/media/guid/2408950221/%s?mbr=true&manifest=m3u' % urls_info.get('content_id'),
                {'force_smil_url': True}),
            'id': urls_info.get('content_id'),
        }
