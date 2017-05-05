# coding: utf-8
from __future__ import unicode_literals

import re
import time

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse_unquote,
    compat_urllib_parse_urlparse,
    compat_urllib_request,
    compat_urllib_parse,
    compat_urlparse,
)
from ..utils import (
    ExtractorError,
    float_or_none,
    sanitized_Request,
    unescapeHTML,
    urlencode_postdata,
    USER_AGENTS,
    RegexNotFoundError,
    compat_str,
)


class CeskaTelevizeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:(?:www\.)?ceskatelevize\.cz/ivysilani/|mshokej\.ceskatelevize\.cz/)(?:[^/?#&]+/)*(?P<id>[^/#?]+)'
    _TESTS = [{
        'url': 'http://www.ceskatelevize.cz/ivysilani/ivysilani/10441294653-hyde-park-civilizace/214411058091220',
        'info_dict': {
            'id': '61924494877246241',
            'ext': 'mp4',
            'title': 'Hyde Park Civilizace: Život v Grónsku',
            'description': 'md5:3fec8f6bb497be5cdb0c9e8781076626',
            'thumbnail': r're:^https?://.*\.jpg',
            'duration': 3350,
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }, {
        'url': 'http://www.ceskatelevize.cz/ivysilani/10441294653-hyde-park-civilizace/215411058090502/bonus/20641-bonus-01-en',
        'info_dict': {
            'id': '61924494877028507',
            'ext': 'mp4',
            'title': 'Hyde Park Civilizace: Bonus 01 - En',
            'description': 'English Subtittles',
            'thumbnail': r're:^https?://.*\.jpg',
            'duration': 81.3,
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }, {
        # live stream
        'url': 'http://www.ceskatelevize.cz/ivysilani/zive/ct4/',
        'info_dict': {
            'id': '402',
            'ext': 'mp4',
            'title': r're:^ČT Sport \d{4}-\d{2}-\d{2} \d{2}:\d{2}$',
            'is_live': True,
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
        'skip': 'Georestricted to Czech Republic',
    }, {
        'url': 'http://www.ceskatelevize.cz/ivysilani/embed/iFramePlayer.php?hash=d6a3e1370d2e4fa76296b90bad4dfc19673b641e&IDEC=217 562 22150/0004&channelID=1&width=100%25',
        'only_matching': True,
    }, {
        'url': 'http://mshokej.ceskatelevize.cz/mshokej/zpravy/353352--pastrnak-jsem-rad-ze-jsem-se-rozhodl-prijet-reprezentovat-je-pro-me-cest',
        'info_dict': {
            'id': '61924494877293706',
            'ext': 'mp4',
            'title': 'Článek - MS hokej 2017',
            'duration': 68.8,
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }, {
        'url': 'http://mshokej.ceskatelevize.cz/videoarchiv/rozhovory-a-reportaze/353090--chystany-special-pro-ms-spousta-novinek-a-prime-prenosy-vsech-zapasu',
        'info_dict': {
            'id': '61924494877291670',
            'ext': 'mp4',
            'title': 'videoarchiv - MS hokej 2017',
            'duration': 243.4,
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }]

    def _real_extract(self, url, retries=0):
        playlist_id = self._match_id(url)

        if playlist_id == 'iFramePlayer.php':
            parsed = compat_urlparse.urlparse(url)
            qs_dict = compat_urlparse.parse_qs(parsed.query)
            if qs_dict.get('videoID'):
                playlist_id = qs_dict['videoID'][0]
            elif qs_dict.get('IDEC'):
                playlist_id = qs_dict['IDEC'][0]
            else:
                self._downloader.report_warning("Could not extract ID from iFramePlayer URL %s" % url)

        webpage = self._download_webpage(url, playlist_id)

        NOT_AVAILABLE_STRING = 'This content is not available at your territory due to limited copyright.'
        if '%s</p>' % NOT_AVAILABLE_STRING in webpage:
            raise ExtractorError(NOT_AVAILABLE_STRING, expected=True)
        if 'Neplatný kód pro videopřehrávač' in webpage:
            if retries < 1:
                self._downloader._report_warning('Invalid code on the page, retrying...')
                time.sleep(15)
                return self._real_extract(url, retries + 1)
            else:
                raise ExtractorError('Invalid code supplied for player')

        type_ = None
        episode_id = None
        data = []

        is_mshokej = re.match(r'^https?://mshokej\..*', url)
        if is_mshokej:
            ids = [unescapeHTML(m.group('id')) for m in re.finditer(r'<(?:[^>]*?\b(?:class=["\'](?P<class>[^"\']*)["\']|data-(?:videoarchive_autoplay|id)=["\'](?P<id>[^"\']*)["\']|data-type=["\'](?P<dataType>[^"\']*)["\']))*', webpage)
                   if ((m.group('dataType') and m.group('dataType') == 'media') or
                       m.group('class') and "video-archive__video" in m.group('class')) and
                   m.group('id')
                   ]
            o = set()
            for id in ids:
                if id not in o:
                    data.append({
                        'playlist[0][type]': 'ct24',
                        'playlist[0][id]': id,
                        'requestUrl': url,
                        'requestSource': 'sport',
                        'type': 'dash'
                    })
                    o.add(id)
            if not data:
                raise ExtractorError('Couldn\'t find any video ids')
        else:
            playlist = self._parse_json(
                self._search_regex(
                    r'getPlaylistUrl\(\[({.+?})\]', webpage, 'playlist',
                    default='{}'), playlist_id)
            if playlist:
                type_ = playlist.get('type')
                episode_id = playlist.get('id')

            if not type_:
                type_ = self._html_search_regex(
                    r'getPlaylistUrl\(\[\{"type":"(.+?)","id":".+?"\}\],',
                    webpage, 'type')
            if not episode_id:
                episode_id = self._html_search_regex(
                    r'getPlaylistUrl\(\[\{"type":".+?","id":"(.+?)"\}\],',
                    webpage, 'episode_id')

            data = [{
                'playlist[0][type]': type_,
                'playlist[0][id]': episode_id,
                'requestUrl': compat_urllib_parse_urlparse(url).path,
                'requestSource': 'iVysilani',
            }]

        entries = []

        for data in data:
          for user_agent in (None, USER_AGENTS['Safari']):
            req = sanitized_Request(
                'http://mshokej.ceskatelevize.cz/get-client-playlist' if is_mshokej else
                'http://www.ceskatelevize.cz/ivysilani/ajax/get-client-playlist',
                data=urlencode_postdata(data))

            req.add_header('Content-type', 'application/x-www-form-urlencoded')
            req.add_header('x-addr', '127.0.0.1')
            req.add_header('X-Requested-With', 'XMLHttpRequest')
            if user_agent:
                req.add_header('User-Agent', user_agent)
            req.add_header('Referer', url)

            playlistpage = self._download_json(req, playlist_id, fatal=False)

            if not playlistpage:
                continue

            playlist_url = playlistpage['url']
            if playlist_url == 'error_region':
                raise ExtractorError(NOT_AVAILABLE_STRING, expected=True)

            req = sanitized_Request(compat_urllib_parse_unquote(playlist_url))
            req.add_header('Referer', url)

            playlist_title = self._og_search_title(webpage, default=None) or unescapeHTML(self._search_regex(r'<title[^>]*>(.*)</title', webpage, 'webpage title', fatal=False))
            playlist_description = self._og_search_description(webpage, default=None)

            playlist = self._download_json(req, playlist_id, fatal=False)
            if not playlist:
                continue

            playlist = playlist.get('playlist')
            if not isinstance(playlist, list):
                continue

            playlist_len = len(playlist)

            for num, item in enumerate(playlist):
                is_live = item.get('type') == 'LIVE'
                formats = []
                for format_id, stream_url in item.get('streamUrls', {}).items():
                    if 'playerType=flash' in stream_url:
                        stream_formats = self._extract_m3u8_formats(
                            stream_url, playlist_id, 'mp4', 'm3u8_native',
                            m3u8_id='hls-%s' % format_id, fatal=False)
                    else:
                        stream_formats = self._extract_mpd_formats(
                            stream_url, playlist_id,
                            mpd_id='dash-%s' % format_id, fatal=False)
                    # See https://github.com/rg3/youtube-dl/issues/12119#issuecomment-280037031
                    if format_id == 'audioDescription':
                        for f in stream_formats:
                            f['source_preference'] = -10
                    formats.extend(stream_formats)

                if user_agent and len(entries) == playlist_len:
                    entries[num]['formats'].extend(formats)
                    continue

                item_id = item.get('id') or item['assetId']
                title = item['title']

                duration = float_or_none(item.get('duration'))
                thumbnail = item.get('previewImageUrl')

                subtitles = {}
                if item.get('type') == 'VOD':
                    subs = item.get('subtitles')
                    if subs:
                        subtitles = self.extract_subtitles(episode_id, subs)

                if playlist_len == 1:
                    final_title = playlist_title or title
                    if is_live:
                        final_title = self._live_title(final_title)
                else:
                    final_title = '%s (%s)' % (playlist_title, title)

                entries.append({
                    'id': compat_str(item_id),
                    'title': final_title,
                    'description': playlist_description if playlist_len == 1 else None,
                    'thumbnail': thumbnail,
                    'duration': duration,
                    'formats': formats,
                    'subtitles': subtitles,
                    'is_live': is_live,
                })

        for e in entries:
            self._sort_formats(e['formats'])

        if len(entries) > 1:
            return self.playlist_result(entries, playlist_id, playlist_title, playlist_description)
        else:
            return entries[0]

    def _get_subtitles(self, episode_id, subs):
        original_subtitles = self._download_webpage(
            subs[0]['url'], episode_id, 'Downloading subtitles')
        srt_subs = self._fix_subtitles(original_subtitles)
        return {
            'cs': [{
                'ext': 'srt',
                'data': srt_subs,
            }]
        }

    @staticmethod
    def _fix_subtitles(subtitles):
        """ Convert millisecond-based subtitles to SRT """

        def _msectotimecode(msec):
            """ Helper utility to convert milliseconds to timecode """
            components = []
            for divider in [1000, 60, 60, 100]:
                components.append(msec % divider)
                msec //= divider
            return '{3:02}:{2:02}:{1:02},{0:03}'.format(*components)

        def _fix_subtitle(subtitle):
            for line in subtitle.splitlines():
                m = re.match(r'^\s*([0-9]+);\s*([0-9]+)\s+([0-9]+)\s*$', line)
                if m:
                    yield m.group(1)
                    start, stop = (_msectotimecode(int(t)) for t in m.groups()[1:])
                    yield '{0} --> {1}'.format(start, stop)
                else:
                    yield line

        return '\r\n'.join(_fix_subtitle(subtitles))


class CeskaTelevizePoradyIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?ceskatelevize\.cz/(?!ivysilani)[^?#&]*/(?:(?P<id>\d+)-[^/?#]*|zive-vysilani(?:/[^?#]*)?)/?(?:[?#]|$)'
    _TESTS = [{
        # video with 18+ caution trailer
        'url': 'http://www.ceskatelevize.cz/porady/10520528904-queer/215562210900007-bogotart/',
        'info_dict': {
            'id': '215 562 21090/0007',
            'title': r're:Queer: Bogotart.*',
        },
        'playlist': [{
            'info_dict': {
                'id': '61924494876844842',
                'ext': 'mp4',
                'title': r're:Queer: Bogotart .*\(Varování 18\+\)',
                'duration': 10.2,
            },
        }, {
            'info_dict': {
                'id': '61924494877068022',
                'ext': 'mp4',
                'title': r're:Queer: Bogotart .*\(Queer\)',
                'thumbnail': r're:^https?://.*\.jpg',
                'duration': 1558.3,
            },
        }],
        'params': {
            # m3u8 download
            'skip_download': True,
        },
        'expected_warnings': [r'.*unable to extract.*OpenGraph description.*|.*retrying.*'],
    }, {
        'url': 'http://www.ceskatelevize.cz/sport/zive-vysilani/',
        'info_dict': {
            'title': r're:ČT Sport živě.*',
            'id': '402',
            'ext': 'mp4',
            'is_live': True
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
        'expected_warnings': [r'.*unable to extract.*OpenGraph description.*|.*retrying.*'],
    }, {
        'url': 'http://www.ceskatelevize.cz/ct24/domaci/2101064-line-reky-se-plni-na-nekterych-mistech-plati-pohotovost',
        'info_dict': {
            'id': '2101064',
            'title': 'Řeky se plnily. V Teplicích nad Bečvou byl vyhlášen stav ohrožení',
            'description': 'Kvůli silnému dešti platí v některých regionech Česka výstraha před povodněmi. Na několika místech Moravskoslezského, Zlínského a Olomouckého kraje platí druhý povodňový stupeň, stav pohotovosti. Třetí stupeň povodňové aktivity znamenající ohrožení byl vyhlášen v Teplicích nad Bečvou a na říčce Polančici na Ostravsku. Počasí sledujte zde.',
        },
        'playlist': [{
            'info_dict': {
                'id': "61924494877291243",
                'ext': 'mp4',
                'title': r're:Události.*',
            },
        }, {
            'info_dict': {
                "id": "61924494877291060",
                'ext': 'mp4',
                'title': r're:Studio ČT24.*',
            },
        }, {
            'info_dict': {
                'ext': 'mp4',
                "id": "61924494877291027",
                'title': 'startswith:',
            },
        }, {
            'info_dict': {
                'ext': 'mp4',
                "id": "61924494877291070",
                'title': 'startswith:',
            },
        }, {
            'info_dict': {
                'ext': 'mp4',
                "id": "61924494877291208",
                'title': 'startswith:',
            },
        },
        ],
        'params': {
            # m3u8 download
            'skip_download': True,
        },
        'expected_warnings': [r'.*unable to extract.*OpenGraph description.*|.*retrying.*'],
    }, {
        'url': 'http://www.ceskatelevize.cz/sport/nejlepsi-videa/353066-ogier-i-meeke-meli-v-argentine-nehodu-v-cele-je-evans/',
        'params': {
            # m3u8 download
            'skip_download': True,
        },
        'info_dict': {
            'id': "61924494877291497",
            "ext": "mp4",
            'title': r're:Ogier i Meeke měli v Argentině nehodu, v čele je Evans.*',
        },
        'expected_warnings': [r'.*unable to extract.*OpenGraph description.*|.*retrying.*'],
    }, {
        'url': 'http://www.ceskatelevize.cz/sport/fotbal/1-liga/352926-fotbal-extra-jaroslav-starka-s-pribrami-na-vecne-casy-a-nikdy-jinak/',
        'params': {
            # m3u8 download
            'skip_download': True,
        },
        'info_dict': {
            "id": "61924494877290816",
            'title': r're:Starka: S negativní publicitou jsem se naučil žít.*',
            "ext": "mp4",
        },
        'expected_warnings': [r'.*unable to extract.*OpenGraph description.*|.*retrying.*'],
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        hash_if_any = self._search_regex(
            r'media_ivysilani:{hash:"(?P<hash>\w+)',
            webpage, 'hash for iVysilani', group='hash', default=None)

        def fixup_hash(data_url):
            if re.search(r'[&?]hash=', data_url) is None and hash_if_any:
                return data_url + "&hash=" + hash_if_any
            else:
                return data_url

        # This would be so much easier with XPath
        webpage_nolive = re.sub(r'(?s)<section\b[^>]*\bid=[\'"]live.*?</section>', '', webpage)

        matches = [compat_urlparse.urljoin('http://www.ceskatelevize.cz', fixup_hash(unescapeHTML(m.group('url')))) for m in
                   re.finditer(r'(?:<span[^>]*\bdata-url=|<iframe[^>]*\bsrc=)(["\'])(?P<url>[^"\']*)["\']',
                               webpage_nolive)
                   if "/ivysilani/" in m.group('url')
                   ]

        ajaxUrl = self._search_regex(r'CT_VideoPlayer.config.ajaxUrl\s*=\s*\'([^\']*)\'',
                                     webpage, 'video player ajax URL', default='/sport/ajax')

        def processMatch(href):
            match1 = re.search(r'\bq=\'([^\']*)\'', href)
            if not match1:
                return ''
            json = self._download_json(
                compat_urllib_request.Request(compat_urlparse.urljoin('http://www.ceskatelevize.cz', ajaxUrl),
                                              compat_urllib_parse.urlencode([('cmd', 'getVideoPlayerUrl'), ('q', match1.group(1)), ('autoStart', 'true')]), headers={'Content-Type': 'application/x-www-form-urlencoded'}),
                video_id)
            return compat_urlparse.urljoin('http://www.ceskatelevize.cz', json['videoPlayerUrl'])

        matches2 = [processMatch(unescapeHTML(m.group('href'))) for m in
                    re.finditer(r'<(?:[^>]*?\b(?:id=["\'](?P<id>[^"\']*)["\']|href=(["\'])(?P<href>(?:(?!\1).)*)["\']))*',
                                webpage)
                    if m.group('id') and "videoItem" in m.group('id') and m.group('href')
                    ]

        matches = matches + [m for m in matches2 if m]
        if not matches:
            raise RegexNotFoundError('Unable to extract iframe player URL')

        title = self._og_search_title(webpage)
        ret = self.playlist_from_matches(matches, video_id=video_id, video_title=title, ie=CeskaTelevizeIE.ie_key())
        if len(ret['entries']) == 1:
            ret = ret['entries'][0]

        def set_if_any(info, key, data):
            if data:
                info[key] = data

        set_if_any(ret, 'thumbnail', self._og_search_thumbnail(webpage))
        set_if_any(ret, 'description', self._og_search_description(webpage))

        return ret
