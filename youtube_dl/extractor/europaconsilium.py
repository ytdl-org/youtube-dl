# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    NO_DEFAULT,
    smuggle_url,
    str_or_none,
)


class EuropaConsiliumIE(InfoExtractor):
    _VALID_URL = r'https?://video.consilium.europa.eu/(?P<lang>[a-z]{2})/(?:webcast|embed)/(?P<id>[a-f0-9-]+)'
    _TEST = {
        'url': 'https://video.consilium.europa.eu/en/webcast/6c841728-4a85-40ac-8536-5b91f1a65fa9',
        'md5': 'befcce5d4de2ba9b045680135ccfe3bc',
        'info_dict': {
            'id': '0_2sj82qqy',
            'ext': 'mp4',
            'title': 'Agriculture and Fisheries Council  - Public session',
            'timestamp': 1551889485,
            'upload_date': '20190318',
            'uploader_id': 'cms',
        }
    }

    def _real_extract(self, url):
        lang, video_id = re.match(self._VALID_URL, url).groups()
        info = self._download_json(
            'https://councilconnect.streamamg.com/api/%s/webcasts/%s' % (
                lang, video_id), video_id)
        entry_id = info['EntryId']
        webpage = self._download_webpage(url, video_id, fatal=False)
        partner_id = '3000261'
        if webpage:
            partner_id = self._search_regex(
                r'data-partnerid\s*=\s*(["\'])(?P<id>\d+)\1', webpage,
                'partner id', default=partner_id, fatal=False, group='id')

        return {
            '_type': 'url_transparent',
            'url': smuggle_url('kaltura:%s:%s' % (partner_id, entry_id), {'service_url': 'https://open.http.mp.streamamg.com'}),
            'ie_key': 'Kaltura',
            'title': self._og_search_title(webpage, default=info.get('Title') or NO_DEFAULT),
            'thumbnail': self._og_search_thumbnail(webpage),
            'upload_date': str_or_none(info.get('ScheduleDay')),
        }
