# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    ExtractorError,
    GeoRestrictedError,
    int_or_none,
    merge_dicts,
    parse_iso8601,
    parse_qs,
    strip_or_none,
    traverse_obj,
    url_or_none,
    urljoin,
)


class ArteTVBaseIE(InfoExtractor):
    _ARTE_LANGUAGES = 'fr|de|en|es|it|pl'
    _API_BASE = 'https://api.arte.tv/api/player/v2'

    # yt-dlp shims

    @classmethod
    def _match_valid_url(cls, url):
        return re.match(cls._VALID_URL, url)

    def _extract_m3u8_formats_and_subtitles(self, *args, **kwargs):
        return self._extract_m3u8_formats(*args, **kwargs), {}


class ArteTVIE(ArteTVBaseIE):
    _VALID_URL = r'''(?x)
                    (?:https?://
                        (?:
                            (?:www\.)?arte\.tv/(?P<lang>%(langs)s)/videos|
                            api\.arte\.tv/api/player/v\d+/config/(?P<lang_2>%(langs)s)
                        )
                    |arte://program)
                        /(?P<id>\d{6}-\d{3}-[AF]|LIVE)
                    ''' % {'langs': ArteTVBaseIE._ARTE_LANGUAGES}
    _TESTS = [{
        'url': 'https://www.arte.tv/en/videos/088501-000-A/mexico-stealing-petrol-to-survive/',
        'only_matching': True,
    }, {
        'url': 'https://www.arte.tv/pl/videos/100103-000-A/usa-dyskryminacja-na-porodowce/',
        'info_dict': {
            'id': '100103-000-A',
            'title': 'USA: Dyskryminacja na porodówce',
            'description': 'md5:242017b7cce59ffae340a54baefcafb1',
            'alt_title': 'ARTE Reportage',
            'timestamp': 1604417980,
            'upload_date': '20201103',
            'duration': 554,
            # test format sort
            'height': 720,
            'thumbnail': r're:https://api-cdn\.arte\.tv/.+940x530',
            'ext': 'mp4',
        },
        'params': {
            'format': 'bestvideo',
            'skip_download': 'm3u8',
        },
    }, {
        'note': 'No alt_title',
        'url': 'https://www.arte.tv/fr/videos/110371-000-A/la-chaleur-supplice-des-arbres-de-rue/',
        'info_dict': {
            'id': '110371-000-A',
            'ext': 'mp4',
            'upload_date': '20220718',
            'duration': 154,
            'timestamp': 1658162460,
            'description': 'md5:5890f36fe7dccfadb8b7c0891de54786',
            'title': 'La chaleur, supplice des arbres de rue',
            'thumbnail': 'https://api-cdn.arte.tv/img/v2/image/CPE2sQDtD8GLQgt8DuYHLf/940x530',
        },
        'params': {
            'format': 'bestvideo',
            'skip_download': 'm3u8',
        },
    }, {
        'url': 'https://api.arte.tv/api/player/v2/config/de/100605-013-A',
        'only_matching': True,
    }, {
        'url': 'https://api.arte.tv/api/player/v2/config/de/LIVE',
        'only_matching': True,
    }]

    _GEO_BYPASS = True

    _LANG_MAP = {  # ISO639 -> French abbreviations
        'r': 'F',
        'de': 'A',
        'en': 'E[ANG]',
        'es': 'E[ESP]',
        'it': 'E[ITA]',
        'pl': 'E[POL]',
        # XXX: probably means mixed; <https://www.arte.tv/en/videos/107710-029-A/dispatches-from-ukraine-local-journalists-report/>
        # uses this code for audio that happens to be in Ukrainian, but the manifest uses the ISO code 'mul' (mixed)
        'mul': 'EU',
    }

    _VERSION_CODE_RE = re.compile(r'''(?x)
        V
        (?P<original_voice>O?)
        (?P<vlang>[FA]|E\[[A-Z]+\]|EU)?
        (?P<audio_desc>AUD|)
        (?:
            (?P<has_sub>-ST)
            (?P<sdh_sub>M?)
            (?P<sub_lang>[FA]|E\[[A-Z]+\]|EU)
        )?
    ''')

    # all obtained by exhaustive testing
    _COUNTRIES_MAP = {
        'DE_FR': (
            'BL', 'DE', 'FR', 'GF', 'GP', 'MF', 'MQ', 'NC',
            'PF', 'PM', 'RE', 'WF', 'YT',
        ),
        # with both of the below 'BE' sometimes works, sometimes doesn't
        'EUR_DE_FR': (
            'AT', 'BL', 'CH', 'DE', 'FR', 'GF', 'GP', 'LI',
            'MC', 'MF', 'MQ', 'NC', 'PF', 'PM', 'RE', 'WF',
            'YT',
        ),
        'SAT': (
            'AD', 'AT', 'AX', 'BG', 'BL', 'CH', 'CY', 'CZ',
            'DE', 'DK', 'EE', 'ES', 'FI', 'FR', 'GB', 'GF',
            'GR', 'HR', 'HU', 'IE', 'IS', 'IT', 'KN', 'LI',
            'LT', 'LU', 'LV', 'MC', 'MF', 'MQ', 'MT', 'NC',
            'NL', 'NO', 'PF', 'PL', 'PM', 'PT', 'RE', 'RO',
            'SE', 'SI', 'SK', 'SM', 'VA', 'WF', 'YT',
        ),
    }

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        video_id = mobj.group('id')
        lang = mobj.group('lang') or mobj.group('lang_2')
        language_code = self._LANG_MAP.get(lang)

        config = self._download_json('{0}/config/{1}/{2}'.format(self._API_BASE, lang, video_id), video_id)

        geoblocking = traverse_obj(config, ('data', 'attributes', 'restriction', 'geoblocking')) or {}
        if geoblocking.get('restrictedArea'):
            raise GeoRestrictedError('Video restricted to {0!r}'.format(geoblocking['code']),
                                     countries=self._COUNTRIES_MAP.get(geoblocking['code'], ('DE', 'FR')))

        if not traverse_obj(config, ('data', 'attributes', 'rights')):
            # Eg: https://www.arte.tv/de/videos/097407-215-A/28-minuten
            # Eg: https://www.arte.tv/es/videos/104351-002-A/serviteur-du-peuple-1-23
            raise ExtractorError(
                'Video is not available in this language edition of Arte or broadcast rights expired', expected=True)

        formats, subtitles = [], {}
        secondary_formats = []
        for stream in config['data']['attributes']['streams']:
            # official player contains code like `e.get("versions")[0].eStat.ml5`
            stream_version = stream['versions'][0]
            stream_version_code = stream_version['eStat']['ml5']

            lang_pref = -1
            m = self._VERSION_CODE_RE.match(stream_version_code)
            if m:
                lang_pref = int(''.join('01'[x] for x in (
                    m.group('vlang') == language_code,      # we prefer voice in the requested language
                    not m.group('audio_desc'),              # and not the audio description version
                    bool(m.group('original_voice')),        # but if voice is not in the requested language, at least choose the original voice
                    m.group('sub_lang') == language_code,   # if subtitles are present, we prefer them in the requested language
                    not m.group('has_sub'),                 # but we prefer no subtitles otherwise
                    not m.group('sdh_sub'),                 # and we prefer not the hard-of-hearing subtitles if there are subtitles
                )))

            short_label = traverse_obj(stream_version, 'shortLabel', expected_type=compat_str, default='?')
            if stream['protocol'].startswith('HLS'):
                fmts, subs = self._extract_m3u8_formats_and_subtitles(
                    stream['url'], video_id=video_id, ext='mp4', m3u8_id=stream_version_code, fatal=False)
                for fmt in fmts:
                    fmt.update({
                        'format_note': '{0} [{1}]'.format(stream_version.get("label", "unknown"), short_label),
                        'language_preference': lang_pref,
                    })
                if any(map(short_label.startswith, ('cc', 'OGsub'))):
                    secondary_formats.extend(fmts)
                else:
                    formats.extend(fmts)
                for sub in subs:
                    subtitles = self._merge_subtitles(subtitles, sub)

            elif stream['protocol'] in ('HTTPS', 'RTMP'):
                formats.append({
                    'format_id': '{0}-{1}'.format(stream["protocol"], stream_version_code),
                    'url': stream['url'],
                    'format_note': '{0} [{1}]'.format(stream_version.get("label", "unknown"), short_label),
                    'language_preference': lang_pref,
                    # 'ext': 'mp4',  # XXX: may or may not be necessary, at least for HTTPS
                })

            else:
                self.report_warning('Skipping stream with unknown protocol {0}'.format(stream["protocol"]))

            # TODO: chapters from stream['segments']?
            # The JS also looks for chapters in config['data']['attributes']['chapters'],
            # but I am yet to find a video having those

        formats.extend(secondary_formats)
        self._remove_duplicate_formats(formats)
        self._sort_formats(formats)

        metadata = config['data']['attributes']['metadata']

        return {
            'id': metadata['providerId'],
            'webpage_url': traverse_obj(metadata, ('link', 'url')),
            'title': traverse_obj(metadata, 'subtitle', 'title'),
            'alt_title': metadata.get('subtitle') and metadata.get('title'),
            'description': metadata.get('description'),
            'duration': traverse_obj(metadata, ('duration', 'seconds')),
            'language': metadata.get('language'),
            'timestamp': traverse_obj(config, ('data', 'attributes', 'rights', 'begin'), expected_type=parse_iso8601),
            'is_live': config['data']['attributes'].get('live', False),
            'formats': formats,
            'subtitles': subtitles,
            'thumbnails': [
                {'url': image['url'], 'id': image.get('caption')}
                for image in metadata.get('images') or [] if url_or_none(image.get('url'))
            ],
        }


class ArteTVEmbedIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?arte\.tv/player/v\d+/index\.php\?.*?\bjson_url=.+'
    _EMBED_REGEX = [r'<(?:iframe|script)[^>]+src=(["\'])(?P<url>(?:https?:)?//(?:www\.)?arte\.tv/player/v\d+/index\.php\?.*?\bjson_url=.+?)\1']
    _TESTS = [{
        'url': 'https://www.arte.tv/player/v5/index.php?json_url=https%3A%2F%2Fapi.arte.tv%2Fapi%2Fplayer%2Fv2%2Fconfig%2Fde%2F100605-013-A&lang=de&autoplay=true&mute=0100605-013-A',
        'only_matching': True,
        'skip': 'Video is not available in this language edition of Arte or broadcast rights expired'
    }, {
        'url': 'https://www.arte.tv/player/v5/index.php?json_url=https%3A%2F%2Fapi.arte.tv%2Fapi%2Fplayer%2Fv2%2Fconfig%2Fpl%2F100103-000-A&lang=pl&autoplay=true&mute=100103-000-A',
        'info_dict': {
            'id': '100103-000-A',
            'ext': 'mp4',
            'title': 'USA: Dyskryminacja na porodówce',
            'timestamp': 1604417980,
            'upload_date': '20201103',
            'description': 'md5:242017b7cce59ffae340a54baefcafb1',
            'duration': 554,
        },
        'params': {
            'format': 'bestvideo',
            'skip_download': 'm3u8',
        },
    }, {
        'url': 'https://www.arte.tv/player/v3/index.php?json_url=https://api.arte.tv/api/player/v2/config/de/100605-013-A',
        'only_matching': True,
    }]

    @classmethod
    def _extract_urls(cls, webpage):
        import itertools    # just until this is lifted into IE
        return list(itertools.chain(*(
            (url for _, url in re.findall(erx, webpage)) for erx in cls._EMBED_REGEX)
        ))

    def _real_extract(self, url):
        qs = parse_qs(url)
        json_url = qs['json_url'][-1]
        video_id = ArteTVIE._match_id(json_url)
        return self.url_result(
            json_url, ie=ArteTVIE.ie_key(), video_id=video_id)


class ArteTVPlaylistIE(ArteTVBaseIE):
    _VALID_URL = r'https?://(?:www\.)?arte\.tv/(?P<lang>%s)/videos/(?P<id>RC-\d{6})' % ArteTVBaseIE._ARTE_LANGUAGES
    _TESTS = [{
        'url': 'https://www.arte.tv/en/videos/RC-016954/earn-a-living/',
        'only_matching': True,
    }, {
        'url': 'https://www.arte.tv/pl/videos/RC-014123/arte-reportage/',
        'playlist_mincount': 100,
        'info_dict': {
            'description': 'md5:84e7bf1feda248bc325ebfac818c476e',
            'id': 'RC-014123',
            'title': 'ARTE Reportage - najlepsze reportaże',
        },
        'skip': '404 Not Found',
    }, {
        'url': 'https://www.arte.tv/en/videos/RC-016979/war-in-ukraine/',
        'playlist_mincount': 79,
        'info_dict': {
            'id': 'RC-016979',
            'title': 'War in Ukraine',
            'description': 'On 24 February, Russian armed forces invaded Ukraine. We follow the war day by day and provide background information with special insights, reports and documentaries.',
        },
    }]

    def _real_extract(self, url):
        lang, playlist_id = self._match_valid_url(url).group('lang', 'id')
        playlist = self._download_json(
            '{0}/playlist/{1}/{2}'.format(self._API_BASE, lang, playlist_id), playlist_id)['data']['attributes']

        entries = [{
            '_type': 'url_transparent',
            'url': video['config']['url'],
            'ie_key': ArteTVIE.ie_key(),
            'id': video.get('providerId'),
            'title': video.get('title'),
            'alt_title': video.get('subtitle'),
            'thumbnail': url_or_none(traverse_obj(video, ('mainImage', 'url'))),
            'duration': int_or_none(traverse_obj(video, ('duration', 'seconds'))),
        } for video in traverse_obj(playlist, ('items', lambda _, v: v['config']['url']))]

        return self.playlist_result(entries, playlist_id,
                                    traverse_obj(playlist, ('metadata', 'title')),
                                    traverse_obj(playlist, ('metadata', 'description')))


class ArteTVCategoryIE(ArteTVBaseIE):
    _VALID_URL = r'https?://(?:www\.)?arte\.tv/(?P<lang>%s)/videos/(?P<id>[\w-]+(?:/[\w-]+)*)/?\s*$' % ArteTVBaseIE._ARTE_LANGUAGES
    _TESTS = [{
        'url': 'https://www.arte.tv/en/videos/politics-and-society/',
        'info_dict': {
            'id': 'politics-and-society',
            'title': 'Politics and society',
            'description': 'Watch documentaries and reportage about politics, society and current affairs.',
        },
        'playlist_mincount': 13,
    }]

    @classmethod
    def suitable(cls, url):
        return (
            not any(ie.suitable(url) for ie in (ArteTVIE, ArteTVPlaylistIE, ))
            and super(ArteTVCategoryIE, cls).suitable(url))

    def _real_extract(self, url):
        lang, playlist_id = self._match_valid_url(url).groups()
        webpage = self._download_webpage(url, playlist_id)

        items = []
        for video in re.finditer(
                r'<a\b[^>]+\bhref\s*=\s*(?P<q>"|\'|\b)(?P<url>(?:https?://www\.arte\.tv)?/%s/videos/[\w/-]+)(?P=q)' % lang,
                webpage):
            video = urljoin(url, video.group('url'))
            if video == url:
                continue
            if any(ie.suitable(video) for ie in (ArteTVIE, ArteTVPlaylistIE, )):
                items.append(video)

        title = (self._og_search_title(webpage, default=None)
                 or self._html_search_regex(r'<title\b[^>]*>([^<]+)</title>', default=None))
        title = strip_or_none(title.rsplit('|', 1)[0]) or self._generic_title(url)

        return merge_dicts(
            self.playlist_from_matches(items, playlist_id=playlist_id, playlist_title=title),
            {'description': self._og_search_description(webpage, default=None)})
