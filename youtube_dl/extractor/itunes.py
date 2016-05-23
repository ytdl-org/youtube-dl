# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor

from ..utils import (
    extract_attributes,
    int_or_none,
    unescapeHTML,
    unified_strdate,
)


class iTunesIE(InfoExtractor):
    _VALID_URL = r'https?://itunes\.apple\.com/[a-z]{2}/[a-z0-9-]+/(?P<display_id>[a-z0-9-]+)?/(?:id)?(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://itunes.apple.com/us/itunes-u/uc-davis-symphony-orchestra/id403834767',
        'info_dict': {
            'id': '403834767',
            'title': 'UC Davis Symphony Orchestra & University Chorus',
        },
        'playlist_count': 31,
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        playlist_id, display_id = mobj.group('id', 'display_id')
        if not display_id:
            display_id = playlist_id

        webpage = self._download_webpage(url, display_id)

        video_infos = re.findall(r'var\s+__desc_popup_d_\d+\s*=\s*({[^><]+});', webpage)
        html_entries = re.findall(r'<tr\s+[^>]*role="row"[^>]+>', webpage)

        entries = []
        for idx, html_entry in enumerate(html_entries):
            video_info = self._parse_json(video_infos[idx], display_id)
            entry = extract_attributes(html_entry)
            entries.append({
                'id': entry['adam-id'],
                'title': entry['preview-title'],
                'description': video_info.get('description'),
                'url': entry.get('audio-preview-url', entry.get('video-preview-url')),
                'duration': int_or_none(entry.get('duration')),
                'release_date': unified_strdate(video_info.get('release_date')),
                'track': unescapeHTML(entry.get('preview-title')),
                'track_number': int_or_none(entry.get('row-number')),
                'track_id': entry.get('adam-id'),
                'artist': unescapeHTML(entry.get('preview-artist')),
                'album': unescapeHTML(entry.get('preview-album')),
            })

        title = self._html_search_regex(r'<h1>(.+)</h1>',
            webpage, 'title')

        return self.playlist_result(entries, playlist_id, title)
