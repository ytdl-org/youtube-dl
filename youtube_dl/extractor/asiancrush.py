# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .kaltura import KalturaIE
from ..utils import extract_attributes


class AsianCrushIE(InfoExtractor):
    _VALID_URL_BASE = r'https?://(?:www\.)?(?P<host>(?:(?:asiancrush|yuyutv|midnightpulp)\.com|cocoro\.tv))'
    _VALID_URL = r'%s/video/(?:[^/]+/)?0+(?P<id>\d+)v\b' % _VALID_URL_BASE
    _TESTS = [{
        'url': 'https://www.asiancrush.com/video/012869v/women-who-flirt/',
        'md5': 'c3b740e48d0ba002a42c0b72857beae6',
        'info_dict': {
            'id': '1_y4tmjm5r',
            'ext': 'mp4',
            'title': 'Women Who Flirt',
            'description': 'md5:7e986615808bcfb11756eb503a751487',
            'timestamp': 1496936429,
            'upload_date': '20170608',
            'uploader_id': 'craig@crifkin.com',
        },
    }, {
        'url': 'https://www.asiancrush.com/video/she-was-pretty/011886v-pretty-episode-3/',
        'only_matching': True,
    }, {
        'url': 'https://www.yuyutv.com/video/013886v/the-act-of-killing/',
        'only_matching': True,
    }, {
        'url': 'https://www.yuyutv.com/video/peep-show/013922v-warring-factions/',
        'only_matching': True,
    }, {
        'url': 'https://www.midnightpulp.com/video/010400v/drifters/',
        'only_matching': True,
    }, {
        'url': 'https://www.midnightpulp.com/video/mononoke/016378v-zashikiwarashi-part-1/',
        'only_matching': True,
    }, {
        'url': 'https://www.cocoro.tv/video/the-wonderful-wizard-of-oz/008878v-the-wonderful-wizard-of-oz-ep01/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        host = mobj.group('host')
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)

        entry_id, partner_id, title = [None] * 3

        vars = self._parse_json(
            self._search_regex(
                r'iEmbedVars\s*=\s*({.+?})', webpage, 'embed vars',
                default='{}'), video_id, fatal=False)
        if vars:
            entry_id = vars.get('entry_id')
            partner_id = vars.get('partner_id')
            title = vars.get('vid_label')

        if not entry_id:
            entry_id = self._search_regex(
                r'\bentry_id["\']\s*:\s*["\'](\d+)', webpage, 'entry id')

        player = self._download_webpage(
            'https://api.%s/embeddedVideoPlayer' % host, video_id,
            query={'id': entry_id})

        kaltura_id = self._search_regex(
            r'entry_id["\']\s*:\s*(["\'])(?P<id>(?:(?!\1).)+)\1', player,
            'kaltura id', group='id')

        if not partner_id:
            partner_id = self._search_regex(
                r'/p(?:artner_id)?/(\d+)', player, 'partner id',
                default='513551')

        description = self._html_search_regex(
            r'(?s)<div[^>]+\bclass=["\']description["\'][^>]*>(.+?)</div>',
            webpage, 'description', fatal=False)

        return {
            '_type': 'url_transparent',
            'url': 'kaltura:%s:%s' % (partner_id, kaltura_id),
            'ie_key': KalturaIE.ie_key(),
            'id': video_id,
            'title': title,
            'description': description,
        }


class AsianCrushPlaylistIE(InfoExtractor):
    _VALID_URL = r'%s/series/0+(?P<id>\d+)s\b' % AsianCrushIE._VALID_URL_BASE
    _TESTS = [{
        'url': 'https://www.asiancrush.com/series/012481s/scholar-walks-night/',
        'info_dict': {
            'id': '12481',
            'title': 'Scholar Who Walks the Night',
            'description': 'md5:7addd7c5132a09fd4741152d96cce886',
        },
        'playlist_count': 20,
    }, {
        'url': 'https://www.yuyutv.com/series/013920s/peep-show/',
        'only_matching': True,
    }, {
        'url': 'https://www.midnightpulp.com/series/016375s/mononoke/',
        'only_matching': True,
    }, {
        'url': 'https://www.cocoro.tv/series/008549s/the-wonderful-wizard-of-oz/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)

        webpage = self._download_webpage(url, playlist_id)

        entries = []

        for mobj in re.finditer(
                r'<a[^>]+href=(["\'])(?P<url>%s.*?)\1[^>]*>' % AsianCrushIE._VALID_URL,
                webpage):
            attrs = extract_attributes(mobj.group(0))
            if attrs.get('class') == 'clearfix':
                entries.append(self.url_result(
                    mobj.group('url'), ie=AsianCrushIE.ie_key()))

        title = self._html_search_regex(
            r'(?s)<h1\b[^>]\bid=["\']movieTitle[^>]+>(.+?)</h1>', webpage,
            'title', default=None) or self._og_search_title(
            webpage, default=None) or self._html_search_meta(
            'twitter:title', webpage, 'title',
            default=None) or self._search_regex(
            r'<title>([^<]+)</title>', webpage, 'title', fatal=False)
        if title:
            title = re.sub(r'\s*\|\s*.+?$', '', title)

        description = self._og_search_description(
            webpage, default=None) or self._html_search_meta(
            'twitter:description', webpage, 'description', fatal=False)

        return self.playlist_result(entries, playlist_id, title, description)
