# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import clean_html


class ChirbitIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?chirb\.it/(?P<id>[^/]+)'
    _TEST = {
        'url': 'http://chirb.it/PrIPv5',
        'md5': '9847b0dad6ac3e074568bf2cfb197de8',
        'info_dict': {
            'id': 'PrIPv5',
            'display_id': 'kukushtv_1423231243',
            'ext': 'mp3',
            'title': 'Фасадстрой',
            'url': 'http://audio.chirbit.com/kukushtv_1423231243.mp3'
        }
    }

    def _real_extract(self, url):
        audio_linkid = self._match_id(url)
        webpage = self._download_webpage(url, audio_linkid)

        audio_title = self._html_search_regex(r'<h2\s+itemprop="name">(.*?)</h2>', webpage, 'title')
        audio_id = self._html_search_regex(r'\("setFile",\s+"http://audio.chirbit.com/(.*?).mp3"\)', webpage, 'audio ID')
        audio_url = 'http://audio.chirbit.com/' + audio_id + '.mp3';

        return {
            'id': audio_linkid,
            'display_id': audio_id,
            'title': audio_title,
            'url': audio_url
        }

class ChirbitProfileIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?chirbit.com/(?P<id>[^/]+)/?$'
    _TEST = {
        'url': 'http://chirbit.com/ScarletBeauty',
        'playlist_count': 3,
        'info_dict': {
            '_type': 'playlist',
            'title': 'ScarletBeauty',
            'id': 'ScarletBeauty'
        }
    }

    def _real_extract(self, url):
        profile_id = self._match_id(url)

        # Chirbit has a pretty weird "Last Page" navigation behavior.
        # We grab the profile's oldest entry to determine when to
        # stop fetching entries.
        oldestpage = self._download_webpage(url + '/24599', profile_id)
        oldest_page_entries = re.findall(
            r'''soundFile:\s*"http://audio.chirbit.com/(.*?).mp3"''',
            oldestpage);
        oldestentry = clean_html(oldest_page_entries[-1]);

        ids = []
        titles = []
        n = 0
        while True:
            page = self._download_webpage(url + '/' + str(n), profile_id)
            page_ids = re.findall(
                r'''soundFile:\s*"http://audio.chirbit.com/(.*?).mp3"''',
                page);
            page_titles = re.findall(
                r'''<div\s+class="chirbit_title"\s*>(.*?)</div>''',
                page);
            ids += page_ids
            titles += page_titles
            if oldestentry in page_ids:
                break
            n += 1

        entries = []
        i = 0
        for id in ids:
            entries.append({
                'id': id,
                'title': titles[i],
                'url': 'http://audio.chirbit.com/' + id + '.mp3'
            });
            i += 1

        info_dict = {
            '_type': 'playlist',
            'id': profile_id,
            'title': profile_id,
            'entries': entries
        }

        return info_dict;
