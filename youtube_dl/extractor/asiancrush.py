# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .kaltura import KalturaIE
from ..utils import extract_attributes


class AsianCrushIE(InfoExtractor):
    IE_NAME = 'asiancrush'
    _DOMAINS = r'(?:asiancrush\.com|yuyutv\.com|midnightpulp\.com)'
    _VALID_URL = r'https?://(?:www\.)?(?P<host>%s)/video/(?:[^/]+/)?0+(?P<id>\d+)v\b' % _DOMAINS
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
        'md5': '90dc82dfcd52e1f44c0b065bc1dd3827',
        'info_dict': {
            'id': '1_66x4rg7o',
            'ext': 'mp4',
            'title': 'The Act of Killing',
            'description': 'md5:76d745019ef586b3dc59c2a344758741',
            'timestamp': 1557419432,
            'upload_date': '20190509',
            'uploader_id': 'admin@ottera.tv',
        },
    }, {
        'url': 'https://www.yuyutv.com/video/peep-show/013922v-warring-factions/',
        'only_matching': True,
    }, {
        'url': 'https://www.midnightpulp.com/video/010400v/drifters/',
        'md5': '44c7993934434afd7f1ee928ef0f734b',
        'info_dict': {
            'id': '1_sh88xpyz',
            'ext': 'mp4',
            'title': 'Drifters',
            'description': 'md5:beccb5d5d2955d6defbf88ea256607db',
            'timestamp': 1497470628,
            'upload_date': '20170614',
            'uploader_id': 'craig@crifkin.com',
        },
    }, {
        'url': 'https://www.midnightpulp.com/video/mononoke/016378v-zashikiwarashi-part-1/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        host = mobj.group('host')
        video_id = self._match_id(url)
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

        description = self._html_search_regex(r'<div class="description">(.+?)</div>', webpage, 'description', fatal=False, flags=re.DOTALL)

        return {
            '_type': 'url_transparent',
            'url': 'kaltura:%s:%s' % (partner_id, kaltura_id),
            'ie_key': KalturaIE.ie_key(),
            'id': video_id,
            'title': title,
            'description': description,
        }


class AsianCrushPlaylistIE(InfoExtractor):
    _VIDEO_IE = AsianCrushIE
    _DOMAINS = r'(?:asiancrush\.com|yuyutv\.com|midnightpulp\.com)'
    _VALID_URL = r'https?://(?:www\.)?(?P<host>%s)/series/0+(?P<id>\d+)s\b' % _DOMAINS
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
        'info_dict': {
            'id': '13920',
            'title': 'Peep Show',
            'description': 'md5:15b59e05eb41fd2082671577eaf1b02d',
        },
        'playlist_count': 54,
    }, {
        'url': 'https://www.midnightpulp.com/series/016375s/mononoke/',
        'info_dict': {
            'id': '16375',
            'title': 'Mononoke',
            'description': 'md5:4a6d4f36eb1165f1854dbc9ac3b83c07',
        },
        'playlist_count': 12,
    }]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)

        webpage = self._download_webpage(url, playlist_id)

        entries = []

        for mobj in re.finditer(
                r'<a[^>]+href=(["\'])(?P<url>%s.*?)\1[^>]*>' % self._VIDEO_IE._VALID_URL,
                webpage):
            attrs = extract_attributes(mobj.group(0))
            if attrs.get('class') == 'clearfix':
                entries.append(self.url_result(
                    mobj.group('url'), ie=self._VIDEO_IE.ie_key()))

        title = re.sub(r'\s*\|\s*.+?$', '',
                       self._html_search_regex(
                           r'(?s)<h1\b[^>]\bid=["\']movieTitle[^>]+>(.+?)</h1>', webpage,
                           'title', default=None) or self._og_search_title(
                           webpage, default=None) or self._html_search_meta(
                           'twitter:title', webpage, 'title',
                           default=None) or self._search_regex(
                           r'<title>([^<]+)</title>', webpage, 'title', fatal=False)
                       )

        description = self._og_search_description(
            webpage, default=None) or self._html_search_meta(
            'twitter:description', webpage, 'description', fatal=False)

        return self.playlist_result(entries, playlist_id, title, description)
