# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

import json


class CpacIE(InfoExtractor):
    IE_NAME = 'cpac'
    _VALID_URL = r'https?://(?:www\.)?cpac\.ca/(.*)/programs/(.*)/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.cpac.ca/en/programs/primetime-politics/episodes/65490909',
        'md5': 'cdbe2b9a46f24ddc0d137264b8c8b14d',
        'info_dict': {
            'id': '65490909',
            'ext': 'mp4',
            'title': 'Auditor General Targets Fighter Jet Program, CRA –  November 20, 2018',
            'description': 'Full coverage of the latest round of auditor general reports on fighter jets, the Canadian Revenue Agency, and more. We hear from officials from the Office of the Auditor General, Defence Minister Harjit Sajjan, MPs, and taxpayers’ ombudsman Sherra Profit. \nWith the price gap growing between Canadian and American oil, we hear about the economic impact from Saskatchewan Energy and Natural Resources Minister Minister Bronwyn Eyre.\n',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        raw_data = self._html_search_regex(r'<script type="application\/ld\+json">([^>]+)<\/script>', webpage, 'json')
        data = json.loads(raw_data)
        formats = self._extract_m3u8_formats(data['contentUrl'], video_id, ext='mp4')
        title = data['name']
        description = data['description']
        return {
            'id': video_id,
            'formats': formats,
            'title': title,
            'description': description,
        }
