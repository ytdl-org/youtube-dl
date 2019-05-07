# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    try_get,
    unified_strdate,
    unified_timestamp,
)


class P3IE(InfoExtractor):
    _VALID_URL = r'https?://(?P<name>[a-z]+)\.p3\.no/(episoder/sesong-(?P<season>\d+)/episode-(?P<episode>\d+)/?|\d{4}/\d{2}/\d{2})/(?P<id>[^/]*)/?'
    _TESTS = [
        {
            'url': 'https://blank.p3.no/2019/03/17/sees-24-mars/',
            'info_dict': {
                'id': 'blank-sees-24-mars',
                'title': 'Sees 24. mars',
                'ext': 'mp4',
                'upload_date': '20190317',
                'description': 'Zehra er 19 år. Hun bor hjemme og studerer farmasi på OsloMet med bestevenninnen Amina.',
                'timestamp': 1552820100,
            },
            'params': {
                'skip_download': True,
            },
        },
        {
            'url': 'http://skam.p3.no/2017/06/24/kjaere-sana/',
            'info_dict': {
                'id': 'skam-kjaere-sana',
                'title': 'Kjære Sana',
                'ext': 'mp4',
                'upload_date': '20170624',
                'description': 'SKAM sesong 4 følger Sana gjennom siste semester i andreklasse på Hartvig Nissen vgs i Oslo.',
                'timestamp': 1498336860,
            },
            'params': {
                'skip_download': True,
            },
        },
        {
            'url': 'http://skam.p3.no/episoder/sesong-1/episode-1/',
            'info_dict': {
                'id': 'skam-s01e01',
                'ext': 'mp4',
                'upload_date': '20150925',
                'title': 'Episode 1:11',
                'description': 'Du ser ut som en slut',
                'timestamp': 1443205800,
            },
            'params': {
                'skip_download': True,
            },
        }
    ]

    def _real_extract(self, url):
        mobj = re.search(self._VALID_URL, url)
        if mobj.group("season") and mobj.group("episode"):
            video_id = 's%02de%02d' % (int(mobj.group("season")), int(mobj.group("episode")))
        else:
            video_id = self._match_id(url)

        video_id = mobj.group("name") + '-' + video_id
        webpage = self._download_webpage(url, video_id)

        manifest_id = (re.search(r'querySelector\(\'.*?\'\), \'(.*?)\', ludoOptions', webpage) or re.search(r'data-nrk-id="([^"]*)"', webpage)).group(1)
        folder = "clip" if re.search(r'-', manifest_id) else "program"
        meta = self._download_json('https://psapi.nrk.no/playback/manifest/%s/%s' % (folder, manifest_id), video_id, 'Downloading video JSON')

        # video_id = try_get(meta, lambda x: x['id'])
        title = self._html_search_regex(r'<meta name="title" content="([^"]*)"', webpage, "title", group=1)
        description = self._og_search_description(webpage)
        video_url = try_get(meta, lambda x: x['playable']['assets'][0]['url'])
        duration = try_get(meta, lambda x: x['statistics']['conviva']['duration'])
        categories = [try_get(meta, lambda x: x['statistics']['conviva']['custom']['category'])]
        timestamp = unified_timestamp(try_get(meta, lambda x: x['availability']['onDemand']['from']))
        upload_date = unified_strdate(try_get(meta, lambda x: x['availability']['onDemand']['from']))

        subtitles = {}
        subtitle_url = try_get(meta, lambda x: x['playable']['subtitles'][0]['webVtt'])
        if subtitle_url:
            subtitles.setdefault('no', []).append({'url': subtitle_url})

        formats = self._extract_m3u8_formats(video_url, video_id, 'mp4')
        self._sort_formats(formats)

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'description': description,
            'upload_date': upload_date,
            'timestamp': timestamp,
            'duration': duration,
            'categories': categories,
            'subtitles': subtitles,
            'formats': formats,
            'season_number': int_or_none(mobj.group("season")),
            'episode_number': int_or_none(mobj.group("episode")),
        }


class P3HomeIE(InfoExtractor):
    _VALID_URL = r'https?://[a-z]+\.p3\.no/?$'
    _TEST = {
        'url': 'https://blank.p3.no/',
        'info_dict': {
            'id': 'Home',
            'title': 'Blank',
            'ext': 'mp4',
        },
        'params': {
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        playlist_id = 'Home'
        webpage = self._download_webpage(url, playlist_id)

        links = re.findall(r'(?s)<a href="([^"]*)">[^<]*</a>\s*</p>\s*</section>\s*<section class="[^"]*">\s*<div class="flex-video', webpage)
        entries = [self.url_result(link, 'P3') for link in links]

        title = self._html_search_regex(r'<meta name="title" content="([^"]*)"', webpage, "title", group=1)
        title = re.sub('\s*\|.*', '', title)
        description = self._og_search_description(webpage)

        return self.playlist_result(entries, playlist_id, title, description)
