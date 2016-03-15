# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import ExtractorError
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
            'params': {
                # m3u8 download
                'skip_download': True,
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
            'params': {
                # m3u8 download
                'skip_download': True,
            },
        },
        {
            # Youtube embedded video
            'url': 'http://cinemassacre.com/2006/12/07/chronologically-confused-about-bad-movie-and-video-game-sequel-titles/',
            'md5': 'ec9838a5520ef5409b3e4e42fcb0a3b9',
            'info_dict': {
                'id': 'OEVzPCY2T-g',
                'ext': 'webm',
                'title': 'AVGN: Chronologically Confused about Bad Movie and Video Game Sequel Titles',
                'upload_date': '20061207',
                'uploader': 'Cinemassacre',
                'uploader_id': 'JamesNintendoNerd',
                'description': 'md5:784734696c2b8b7f4b8625cc799e07f6',
            }
        },
        {
            # Youtube embedded video
            'url': 'http://cinemassacre.com/2006/09/01/mckids/',
            'md5': '7393c4e0f54602ad110c793eb7a6513a',
            'info_dict': {
                'id': 'FnxsNhuikpo',
                'ext': 'webm',
                'upload_date': '20060901',
                'uploader': 'Cinemassacre Extra',
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
            },
            'params': {
                # m3u8 download
                'skip_download': True,
            },
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
