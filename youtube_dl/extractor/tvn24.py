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
    _VALID_URL = r'https?://(?:(?:[^/]+)\.)?(?:toteraz|tvn24(?:bis)?)\.pl/(?:[^/]+/)*(?P<id>[^/]+)'
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
        # no OpenGraph title or description
        'url': 'https://tvnmeteo.tvn24.pl/magazyny/maja-w-ogrodzie,13/odcinki-online,1,1,1,0/zielona-wstazka-wsrod-pagorkow-odc-705-hgtv-odc-5-serii-2019,1831029.html',
        'md5': '6fc1cdb118e429dd05c7111305caee83',
        'info_dict': {
            'id': '1831029',
            'ext': 'mp4',
            'title': 'Zielona wstążka wśród pagórków (odc. 705 /HGTV odc. 5 serii 2019) - Maja w Ogrodzie',
        }
    }, {
        # no data-quality
        'url': 'https://tvnmeteo.tvn24.pl/informacje-pogoda/swiat,27/kotka-przyjela-cztery-wiewiorki-zaczely-po-niej-biegac-i-skakac,289746,1,0.html',
        'md5': '691d604adc807a84c769c487762fc1ea',
        'info_dict': {
            'id': '1840073',
            'ext': 'mp4',
            'title': 'Kotka przyjęła cztery wiewiórki. "Zaczęły po niej biegać i skakać"',
            'description': 'Kotka o imieniu Pusza, żyjąca w Parku Miniatur w krymskim mieście Bakczysaraj to idealny przykład na to, że matczyna miłość nie zna granic. Zwierzę zao...',
        }
    }, {
        'url': 'https://szklokontaktowe.tvn24.pl/lenin-czyli-kto,932164.html',
        'info_dict': {
            'title': 'Lenin, czyli kto?',
            'description': 'Jarosław Kaczyński zdradził w Nowym Sączu pewną tajemnicę. Teraz już wszyscy wiemy, na którego z przedstawicieli PiS ludzie są tak źli na niego, że go nazy...',
        },
        'playlist_count': 3,
        'playlist': [{
            'md5': '014222e9a6261b424cd3474fd94ffeeb',
            'info_dict': {
                'id': '1841329',
                'ext': 'mp4',
                'title': 'Lenin, czyli kto? - część 1',
            },
        }],
    }, {
        'url': 'https://szklokontaktowe.tvn24.pl/rumba-szuka-domu,931617.html',
        'info_dict': {
            'id': '1840681',
            'ext': 'mp4',
            'title': 'Rumba szuka domu',
            'description': 'RUMBA - wspaniała, ok czteroletnia suczka w typie owczarka uratowana z paskudnego schroniska wypatruje domu. Odznacza się wielką inteligencją i bardzo pozy...',
        }
    }, {
        'url': 'https://toteraz.pl/zakaz-wyprowadzania-psow-nielegalny-decyzja-sadu-administracyjnego,1838704.html',
        'md5': '46d127c478834e942b196d584b3ed747',
        'info_dict': {
            'id': '1838704',
            'ext': 'mp4',
            'title': 'Zakaz wyprowadzania psów nielegalny. Decyzja Sądu Administracyjnego',
            'description': 'Okazuje się, że zakaz wprowadzania psów jest nielegalny i należy go traktować wyłącznie w kategoriach prośby.',
        }
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
                video_id = self._search_regex(
                    r'^(\d{6,})($|_)',
                    extract_value('video-id', 'video id'), 'video id')
                try:
                    title = match.group('title')
                except IndexError:
                    title = None
                title = unescapeHTML(title)
                thumbnail = extract_value('poster', 'thumbnail', fatal=False)
                quality_data = extract_json('quality', 'formats')
                info = {
                    'id': video_id,
                    'thumbnail': thumbnail,
                    'title': title,
                }
                if quality_data:
                    info['formats'] = formats = []
                    for format_id, url in quality_data.items():
                        formats.append({
                            'url': url,
                            'format_id': format_id,
                            'height': int_or_none(format_id.rstrip('p')),
                        })
                    self._sort_formats(formats)
                else:
                    info['url'] = url = extract_value('src', 'video URL')
                    height = self._search_regex('-([0-9]+)p[.]', url, 'format id', default=None)
                    if height:
                        info.update({
                            'format_id': height + 'p',
                            'height': int_or_none(height),
                        })
                entries.append(info)
            if not entries:
                # provoke RegexNotFoundError
                self._search_regex('x', '', 'video elements')
            return entries

        if '/superwizjer-w-tvn24,' in url:
            regex = r'<a\b[^>]*\btitle="(?P<title>[^"]+)"[^>]*\bclass="playVideo">\s*</a>\s*(<[^/][^>]*>\s*)+' + VIDEO_ELT_REGEX
            entries = extract_videos(regex=regex)
        elif '//szklokontaktowe.tvn24.pl/' in url:
            regex = VIDEO_ELT_REGEX + r'(\s*</div>)+\s*<figcaption>'
            entries = extract_videos(regex=regex)
            if len(entries) > 1:
                title = self._og_search_title(webpage)
                for n, entry in enumerate(entries, start=1):
                    entry['title'] = '{title} - część {n}'.format(title=title, n=n)
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
            info['title'] = (self._og_search_title(webpage, default=None) or
                             self._html_search_regex(r'<title>([^<]+)', webpage, 'title'))

        info['description'] = self._og_search_description(webpage, default=None)

        return info
