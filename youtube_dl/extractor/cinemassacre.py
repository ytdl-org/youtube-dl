# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import ExtractorError
from .bliptv import BlipTVIE
from .screenwavemedia import ScreenwaveMediaIE


class CinemassacreIE(InfoExtractor):
    _VALID_URL = 'https?://(?:www\.)?cinemassacre\.com/(?P<date_y>[0-9]{4})/(?P<date_m>[0-9]{2})/(?P<date_d>[0-9]{2})/(?P<display_id>[^?#/]+)'
    _TESTS = [
        {
            'url': 'http://cinemassacre.com/2012/11/10/avgn-the-movie-trailer/',
            'md5': 'fde81fbafaee331785f58cd6c0d46190',
            'info_dict': {
                'id': 'Cinemassacre-19911',
                'ext': 'mp4',
                'upload_date': '20121110',
                'title': '“Angry Video Game Nerd: The Movie” – Trailer',
                'description': 'md5:fb87405fcb42a331742a0dce2708560b',
            },
        },
        {
            'url': 'http://cinemassacre.com/2013/10/02/the-mummys-hand-1940',
            'md5': 'd72f10cd39eac4215048f62ab477a511',
            'info_dict': {
                'id': 'Cinemassacre-521be8ef82b16',
                'ext': 'mp4',
                'upload_date': '20131002',
                'title': 'The Mummy’s Hand (1940)',
            },
        },
        {
            # blip.tv embedded video
            'url': 'http://cinemassacre.com/2006/12/07/chronologically-confused-about-bad-movie-and-video-game-sequel-titles/',
            'md5': 'ca9b3c8dd5a66f9375daeb5135f5a3de',
            'info_dict': {
                'id': '4065369',
                'ext': 'flv',
                'title': 'AVGN: Chronologically Confused about Bad Movie and Video Game Sequel Titles',
                'upload_date': '20061207',
                'uploader': 'cinemassacre',
                'uploader_id': '250778',
                'timestamp': 1283233867,
                'description': 'md5:0a108c78d130676b207d0f6d029ecffd',
            }
        },
        {
            # Youtube embedded video
            'url': 'http://cinemassacre.com/2006/09/01/mckids/',
            'md5': '6eb30961fa795fedc750eac4881ad2e1',
            'info_dict': {
                'id': 'FnxsNhuikpo',
                'ext': 'mp4',
                'upload_date': '20060901',
                'uploader': 'Cinemassacre Extras',
                'description': 'md5:de9b751efa9e45fbaafd9c8a1123ed53',
                'uploader_id': 'Cinemassacre',
                'title': 'AVGN: McKids',
            }
        },
        {
            'url': 'http://cinemassacre.com/2015/05/25/mario-kart-64-nintendo-64-james-mike-mondays/',
            'md5': '1376908e49572389e7b06251a53cdd08',
            'info_dict': {
                'id': 'Cinemassacre-555779690c440',
                'ext': 'mp4',
                'description': 'Let’s Play Mario Kart 64 !! Mario Kart 64 is a classic go-kart racing game released for the Nintendo 64 (N64). Today James & Mike do 4 player Battle Mode with Kyle and Bootsy!',
                'title': 'Mario Kart 64 (Nintendo 64) James & Mike Mondays',
                'upload_date': '20150525',
            }
        }
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        display_id = mobj.group('display_id')
        video_date = mobj.group('date_y') + mobj.group('date_m') + mobj.group('date_d')

        webpage = self._download_webpage(url, display_id)

        playerdata_url = self._search_regex(
            [
                ScreenwaveMediaIE.EMBED_PATTERN,
                r'<iframe[^>]+src="(?P<url>(?:https?:)?//(?:[^.]+\.)?youtube\.com/.+?)"',
            ],
            webpage, 'player data URL', default=None, group='url')
        if not playerdata_url:
            playerdata_url = BlipTVIE._extract_url(webpage)
        if not playerdata_url:
            raise ExtractorError('Unable to find player data')

        video_title = self._html_search_regex(
            r'<title>(?P<title>.+?)\|', webpage, 'title')
        video_description = self._html_search_regex(
            r'<div class="entry-content">(?P<description>.+?)</div>',
            webpage, 'description', flags=re.DOTALL, fatal=False)
        video_thumbnail = self._og_search_thumbnail(webpage)

        return {
            '_type': 'url_transparent',
            'display_id': display_id,
            'title': video_title,
            'description': video_description,
            'upload_date': video_date,
            'thumbnail': video_thumbnail,
            'url': playerdata_url,
        }
