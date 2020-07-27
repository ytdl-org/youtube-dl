# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    ExtractorError,
    try_get,
    float_or_none,
    unified_strdate,
)
import json


class RedBullTVIE(InfoExtractor):
    _VALID_URL = r"""(?x)^
                     https?://
                     (?:www\.)?redbull\.com/
                     [^/]+/  # locale/language code
                     (?:videos|films|episodes)/
                     .+
                     $"""
    _TESTS = [{
        'url': 'https://www.redbull.com/int-en/videos/pedro-barros-concrete-dreams-story-clip',
        'md5': '8e265c207aa7f191dc49505ae599f3ee',
        'info_dict': {
            'id': 'rrn:content:videos:9f804d87-bee9-48fa-aba2-a990c95f9316',
            'ext': 'mp4',
            'title': 'Concrete Dreams - Pedro\'s Niemeyer tour of Brazil',
            'description': 'Pedro Barros had a dream to skate the iconic works of Oscar Niemeyer – one of the pillars of modern world architecture.',
            'duration': 943.0,
            'release_date': '20200618',
        },
    }, {
        'url': 'https://www.redbull.com/int-en/films/against-the-odds',
        'md5': '3a753f7c3c1f9966ae660e05c3c7862b',
        'info_dict': {
            'id': 'rrn:content:films:0825a746-5930-539d-a1dd-d06a7d94ae18',
            'ext': 'mp4',
            'title': 'Against the Odds - The story of a new team coming together',
            'description': 'In 2018, OG were at rock-bottom, hit by painful departures and scrapping in qualifiers for Dota 2\'s TI8. Against the Odds is the fairytale of this broken team\'s shot at Gaming’s biggest prize.',
            'duration': 4837.0,
            'release_date': '20190801',
        },
    }, {
        'url': 'https://www.redbull.com/int-en/episodes/red-bull-moto-spy-s4-e1',
        'md5': '4bee7de8c8caba977f22055d8d32473d',
        'info_dict': {
            'id': 'rrn:content:episode-videos:0f020f53-c089-460e-9740-cfb0b9144cda',
            'ext': 'mp4',
            'title': 'Great characters make great riders - Red Bull Moto Spy S4E1',
            'description': 'The 2020 AMA Supercross season features some talented big-name riders. Are the likes of Cooper Webb, Ken Roczen and half a dozen others destined to dominate – and block the rookies from succeeding?',
            'duration': 1448.0,
            'release_date': '20200102',
        },
    }]

    def _real_extract(self, url):
        # we want to use the rrn ID as the video id, but we can't know it until
        # after downloading the webpage
        webpage = self._download_webpage(url, video_id=url)

        info = json.loads(self._html_search_regex(
            r'<script type="application/ld\+json">(.*?)</script>', webpage, 'video info'))
        rrn_id = self._search_regex(
            r'(rrn:.*):',
            try_get(info, lambda x: x['associatedMedia']['embedUrl'], compat_str)
            or try_get(info, lambda x: x["embedUrl"], compat_str),
            'rrn ID')

        # get access token for download
        session = self._download_json(
            'https://api.redbull.tv/v3/session', rrn_id,
            note='Downloading access token', query={
                'os_family': 'http',
            })
        if session.get('code') == 'error':
            raise ExtractorError('{0} said: {1}'.format(
                self.IE_NAME, session['message']))
        token = session['token']

        # extract formats from m3u8
        # subtitle tracks are also listed in this m3u8, but yt-dl does not
        # currently implement an easy way to download m3u8 VTT subtitles
        formats = self._extract_m3u8_formats(
            'https://dms.redbull.tv/v3/{0}/{1}/playlist.m3u8'.format(rrn_id, token),
            rrn_id, 'mp4', entry_protocol='m3u8_native', m3u8_id='hls')
        self._sort_formats(formats)

        # download more metadata
        metadata = self._download_json(
            'https://api.redbull.tv/v3/products/{0}'.format(rrn_id),
            rrn_id, note='Downloading video information',
            headers={'Authorization': token}
        )

        # extract metadata
        title = try_get(metadata, lambda x: x['title'], compat_str) or \
            try_get(metadata, lambda x: x['analytics']['asset']['title'], compat_str)

        subheading = try_get(metadata, lambda x: x['subheading'], compat_str)
        if subheading:
            title += ' - {0}'.format(subheading)

        long_description = try_get(
            metadata, lambda x: x['long_description'], compat_str)
        short_description = try_get(
            metadata, lambda x: x['short_description'], compat_str)

        duration = float_or_none(try_get(
            metadata, lambda x: x['duration'], int), scale=1000)

        date_pub = try_get(info, lambda x: x['datePublished'], compat_str)
        date_create = try_get(info, lambda x: x['dateCreated'], compat_str)

        return {
            'id': rrn_id,
            'title': title,
            'description': long_description or short_description,
            'duration': duration,
            'release_date': unified_strdate(date_pub or date_create),
            'formats': formats,
        }
