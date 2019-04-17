# coding: utf-8
from __future__ import unicode_literals

import itertools
import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    remove_end,
    unescapeHTML,
)


class TVN24IE(InfoExtractor):
    _VALID_URL = r'https?://(?:(?:[^/]+)\.)?tvn24(?:bis)?\.pl/(?:[^/]+/)*(?P<id>[^/]+)'
    _TESTS = [{
        'url': 'http://www.tvn24.pl/wiadomosci-z-kraju,3/oredzie-artura-andrusa,702428.html',
        'md5': 'fbdec753d7bc29d96036808275f2130c',
        'info_dict': {
            'id': '1584444',
            'ext': 'mp4',
            'title': '"Święta mają być wesołe, dlatego, ludziska, wszyscy pod jemiołę"',
            'description': 'Wyjątkowe orędzie Artura Andrusa, jednego z gości Szkła kontaktowego.',
            'thumbnail': 're:https?://.*[.]jpeg',
        }
    }, {
        'url': 'https://www.tvn24.pl/superwizjer-w-tvn24,149,m/farma-trolli-zarabiaja-na-falszywych-informacjach-i-hejcie,923108.html',
        'md5': 'fbdec753d7bc29d96036808275f2130c',
        'info_dict': {
            'title': '"Ludzie to jest, jakby nie patrzeć, też pieniądz". Farmy trolli zarabiają na fake newsach i hejcie',
            'description': 'Ponad połowa Polaków wierzy w informacje, które znajduje w mediach społecznościowych. Ten fakt wykorzystują anonimowi twórcy tak zwanych fake newsów, czyli...',
        },
        'playlist_count': 4,
        'playlist': [{
            'md5': '8b1001e576a81e22fbb605a9e5ca9d65',
            'info_dict': {
                'id': '1831060',
                'ext': 'mp4',
                'title': 'Farma trolli. Pierwsza część reportażu',
            },
        }],
    }, {
        'url': 'http://fakty.tvn24.pl/ogladaj-online,60/53-konferencja-bezpieczenstwa-w-monachium,716431.html',
        'only_matching': True,
    }, {
        'url': 'http://sport.tvn24.pl/pilka-nozna,105/ligue-1-kamil-glik-rozcial-glowe-monaco-tylko-remisuje-z-bastia,716522.html',
        'only_matching': True,
    }, {
        'url': 'http://tvn24bis.pl/poranek,146,m/gen-koziej-w-tvn24-bis-wracamy-do-czasow-zimnej-wojny,715660.html',
        'only_matching': True,
    }, {
        'url': 'https://www.tvn24.pl/magazyn-tvn24/angie-w-jednej-czwartej-polka-od-szarej-myszki-do-cesarzowej-europy,119,2158',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        page_id = self._match_id(url)
        page_id = remove_end(page_id, '.html')

        webpage = self._download_webpage(url, page_id)

        VIDEO_ELT_REGEX = r'(?P<video><div\b[^>]+\bclass="[^"]*\bvideoPlayer\b[^"]*"[^>]+>)'

        def extract_videos(regex=VIDEO_ELT_REGEX, single=False):

            def extract_value(attr, name, fatal=True):
                return self._html_search_regex(
                    r'\bdata-%s=(["\'])(?P<val>(?!\1).+?)\1' % attr, video_elt,
                    name, group='val', fatal=fatal)

            def extract_json(attr, name, fatal=True):
                value = extract_value(attr, name, fatal=fatal) or '{}'
                return self._parse_json(value, video_id or page_id, fatal=fatal)

            entries = []
            iterator = re.finditer(regex, webpage)
            if single:
                iterator = itertools.islice(iterator, 0, 1)
            for match in iterator:
                video_elt = match.group('video')
                video_id = None
                share_params = extract_json('share-params', 'share params', fatal=False)
                if share_params:
                    video_id = share_params['id']
                else:
                    video_id = extract_value('video-id', 'video id')
                try:
                    title = match.group('title')
                except IndexError:
                    title = None
                title = unescapeHTML(title)
                thumbnail = extract_value('poster', 'thumbnail', fatal=False)
                quality_data = extract_json('quality', 'formats')
                formats = []
                for format_id, url in quality_data.items():
                    formats.append({
                        'url': url,
                        'format_id': format_id,
                        'height': int_or_none(format_id.rstrip('p')),
                    })
                self._sort_formats(formats)
                entries.append({
                    'id': video_id,
                    'thumbnail': thumbnail,
                    'formats': formats,
                    'title': title,
                })
            if not entries:
                # provoke RegexNotFoundError
                self._search_regex('x', '', 'video elements')
            return entries

        if '/superwizjer-w-tvn24,' in url:
            regex = r'<a\b[^>]*\btitle="(?P<title>[^"]+)"[^>]*\bclass="playVideo">\s*</a>\s*(<[^/][^>]*>\s*)+' + VIDEO_ELT_REGEX
            entries = extract_videos(regex=regex)
        else:
            entries = extract_videos(single=True)

        if len(entries) == 1:
            info = entries[0]
        else:
            info = {
                'video_id': page_id,
                '_type': 'multi_video',
                'entries': entries,
            }

        if not info.get('title'):
            info['title'] = self._og_search_title(webpage)
        info['description'] = self._og_search_description(webpage)

        return info
