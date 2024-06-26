# coding: utf-8
from __future__ import unicode_literals

import itertools
import random
import re

from .common import InfoExtractor
from ..compat import (
    compat_HTTPError,
    compat_str,
)
from ..utils import (
    clean_html,
    determine_ext,
    ExtractorError,
    int_or_none,
    js_to_json,
    traverse_obj,
    url_or_none,
)


def txt_or_none(v, default=None):
    return default if v is None else (compat_str(v).strip() or default)

if not hasattr(InfoExtractor, '_match_valid_url'):

    import sys
    from ..compat import (
        compat_os_name,
        compat_re_Pattern as compiled_regex_type,
    )
    from ..utils import (
        bug_reports_message,
        error_to_compat_str,
        NO_DEFAULT,
        RegexNotFoundError,
    )

    BaseIE = InfoExtractor

    class InfoExtractor(BaseIE):
        def _match_valid_url(self, url):
            return re.match(self._VALID_URL, url)

        def _search_regex(self, pattern, string, name, default=NO_DEFAULT, fatal=True, flags=0, group=None):
            """
            Perform a regex search on the given string, using a single or a list of
            patterns returning the first matching group.
            In case of failure return a default value or raise a WARNING or a
            RegexNotFoundError, depending on fatal, specifying the field name.
            """
            if isinstance(pattern, (str, compat_str, compiled_regex_type)):
                mobj = re.search(pattern, string, flags)
            else:
                for p in pattern:
                    mobj = re.search(p, string, flags)
                    if mobj:
                        break

            if not self._downloader.params.get('no_color') and compat_os_name != 'nt' and sys.stderr.isatty():
                _name = '\033[0;34m%s\033[0m' % name
            else:
                _name = name

            if mobj:
                if group is None:
                    # return the first matching group
                    return next(g for g in mobj.groups() if g is not None)
                elif isinstance(group, (list, tuple)):
                    return tuple(mobj.group(g) for g in group)
                else:
                    return mobj.group(group)
            elif default is not NO_DEFAULT:
                return default
            elif fatal:
                raise RegexNotFoundError('Unable to extract %s' % _name)
            else:
                self.report_warning('unable to extract %s' % _name + bug_reports_message())
                return None

        def _html_search_regex(self, pattern, string, name, default=NO_DEFAULT, fatal=True, flags=0, group=None):
            """
            Like _search_regex, but strips HTML tags and unescapes entities.
            """
            res = self._search_regex(pattern, string, name, default, fatal, flags, group)
            if isinstance(res, tuple):
                return tuple(map(clean_html, res))
            return clean_html(res or None)

        def _search_json(self, start_pattern, string, name, video_id, **kwargs):
            """Searches string for the JSON object specified by start_pattern"""

            # self, start_pattern, string, name, video_id, *, end_pattern='',
            # contains_pattern=r'{(?s:.+)}', fatal=True, default=NO_DEFAULT
            end_pattern = kwargs.pop('end_pattern', '')
            contains_pattern = kwargs.pop('contains_pattern', r'{(?:[\s\S]+)}')
            fatal = kwargs.get('fatal', True)
            default = kwargs.get('default', NO_DEFAULT)

            # NB: end_pattern is only used to reduce the size of the initial match
            if default is NO_DEFAULT:
                default, has_default = {}, False
            else:
                fatal, has_default = False, True

            json_string = self._search_regex(
                r'(?:{0})\s*(?P<json>{1})\s*(?:{2})'.format(
                    start_pattern, contains_pattern, end_pattern),
                string, name, group='json', fatal=fatal, default=None if has_default else NO_DEFAULT)
            if not json_string:
                return default

            try:
                # return self._parse_json(json_string, video_id, ignore_extra=True, **kwargs)
                return self._parse_json(json_string, video_id, **kwargs)
            except ExtractorError as e:
                if not self._downloader.params.get('no_color') and compat_os_name != 'nt' and sys.stderr.isatty():
                    _name = '\033[0;34m%s\033[0m' % name
                else:
                    _name = name
                msg = 'Unable to extract {0} - Failed to parse JSON'.format(_name)
                if fatal:
                    raise ExtractorError(msg, cause=e.cause, video_id=video_id)
                elif not has_default:
                    self.report_warning(
                        '{0}: {1}'.format(msg, error_to_compat_str(e)), video_id=video_id)
            return default


class TVPIE(InfoExtractor):
    IE_NAME = 'tvp'
    IE_DESC = 'Telewizja Polska'
    _VALID_URL = r'https?://(?:[^/]+\.)?(?:tvp(?:parlament)?\.(?:pl|info)|polandin\.com|tvpworld\.com|swipeto\.pl)/(?:(?:(?!\d+/)[^/]+/)*|(?:video|website)/[^/]+,)(?P<id>\d+)'
    _TESTS = [{
        # TVPlayer 2 in js wrapper
        'url': 'https://swipeto.pl/64095316/uliczny-foxtrot-wypozyczalnia-kaset-kto-pamieta-dvdvideo',
        'info_dict': {
            'id': '64095316',
            'ext': 'mp4',
            'title': 'Uliczny Foxtrot — Wypożyczalnia kaset. Kto pamięta DVD-Video?',
            'age_limit': 0,
            'duration': 374,
            'thumbnail': r're:https://.+',
        },
        'expected_warnings': [
            'Failed to download ISM manifest: HTTP Error 404: Not Found',
            'Failed to download m3u8 information: HTTP Error 404: Not Found',
        ],
        'skip': 'Video gone: 404 Nie znaleziono obiektu',
    }, {
        # TVPlayer 2 in js wrapper (redirect to VodVideo)
        'url': 'https://vod.tvp.pl/video/czas-honoru,i-seria-odc-13,194536',
        'md5': 'a21eb0aa862f25414430f15fdfb9e76c',
        'info_dict': {
            'id': '194536',
            'ext': 'mp4',
            'title': 'Czas honoru, odc. 13 – Władek',
            'description': 'md5:76649d2014f65c99477be17f23a4dead',
            'age_limit': 12,
        },
        'add_ie': ['Generic', 'TVPEmbed'],
    }, {
        # film (old format)
        'url': 'https://vod.tvp.pl/website/krzysztof-krawczyk-cale-moje-zycie,51374466',
        'info_dict': {
            'id': '51374509',
            'ext': 'mp4',
            'title': 'Krzysztof Krawczyk – całe moje życie, Krzysztof Krawczyk – całe moje życie',
            'description': 'md5:2e80823f00f5fc263555482f76f8fa42',
            'age_limit': 12,
        },
        'params': {
            'skip_download': True,
        },
        'add_ie': ['TVPEmbed'],
        'skip': 'This video is not available from your location due to geo restriction',
    }, {
        # TVPlayer legacy
        'url': 'https://www.tvp.pl/polska-press-video-uploader/wideo/62042351',
        'info_dict': {
            'id': '62042351',
            'ext': 'mp4',
            'title': 'Wideo',
            'description': 'Wideo Kamera',
            'duration': 24,
            'age_limit': 0,
            'thumbnail': r're:https://.+',
        },
        'add_ie': ['TVPEmbed'],
    }, {
        # TVPlayer 2 in iframe
        # page id is not the same as video id(#7799)
        'url': 'https://wiadomosci.tvp.pl/50725617/dzieci-na-sprzedaz-dla-homoseksualistow',
        'md5': 'd35fb45103802488fcb7470e411b9ed4',
        'info_dict': {
            'id': '50725617',
            'ext': 'mp4',
            'title': 'Dzieci na sprzedaż dla homoseksualistów',
            'description': 'md5:7d318eef04e55ddd9f87a8488ac7d590',
            'age_limit': 12,
            'duration': 259,
            'thumbnail': r're:https://.+',
        },
        'add_ie': ['TVPEmbed'],
    }, {
        # TVPlayer 2 in client-side rendered website (regional; window.__newsData)
        'url': 'https://warszawa.tvp.pl/25804446/studio-yayo',
        'info_dict': {
            'id': '25804446',
            'ext': 'mp4',
            'title': 'Studio Yayo',
            'upload_date': '20160616',
            'timestamp': 1466075700,
            'age_limit': 0,
            'duration': 20,
            'thumbnail': r're:https://.+',
        },
        'add_ie': ['TVPEmbed'],
        'skip': 'Video is geo restricted',
    }, {
        # TVPlayer 2 in client-side rendered website (tvp.info; window.__videoData)
        'url': 'https://www.tvp.info/52880236/09042021-0800',
        'info_dict': {
            'id': '52880236',
            'ext': 'mp4',
            'title': '09.04.2021, 08:00',
            'age_limit': 0,
            'thumbnail': r're:https://.+',
        },
        'add_ie': ['TVPEmbed'],
        'skip': 'Video is geo restricted',
    }, {
        # client-side rendered (regional) program (playlist) page
        'url': 'https://opole.tvp.pl/9660819/rozmowa-dnia',
        'info_dict': {
            'id': '9660819',
            'description': 'Od poniedziałku do piątku o 18:55',
            'title': 'Rozmowa dnia',
        },
        'playlist_mincount': 1800,
        'params': {
            'skip_download': True,
        }
    }, {
        # ABC-specific video embeding
        # moved to https://bajkowakraina.tvp.pl/wideo/50981130,teleranek,51027049,zubr,51116450
        'url': 'https://abc.tvp.pl/48636269/zubry-odc-124',
        'info_dict': {
            'id': '48320456',
            'ext': 'mp4',
            'title': 'Teleranek, Żubr',
        },
        'skip': 'Video gone: Nie znaleziono obiektu',
    }, {
        # yet another vue page
        'url': 'https://jp2.tvp.pl/46925618/filmy',
        'info_dict': {
            'id': '46925618',
            'title': 'Filmy',
        },
        'playlist_mincount': 19,
    }, {
        # redirect
        'url': 'https://vod.tvp.pl/48463890/wadowickie-spotkania-z-janem-pawlem-ii',
        'info_dict': {
            'id': '295157',
            'title': 'Wadowickie spotkania z Janem Pawłem II',
        },
        'playlist_mincount': 12,
        'add_ie': ['TVPEmbed', 'TVPVODSeries'],
    }, {
        'url': 'http://vod.tvp.pl/seriale/obyczajowe/na-sygnale/sezon-2-27-/odc-39/17834272',
        'only_matching': True,
    }, {
        'url': 'http://wiadomosci.tvp.pl/25169746/24052016-1200',
        'only_matching': True,
    }, {
        'url': 'http://krakow.tvp.pl/25511623/25lecie-mck-wyjatkowe-miejsce-na-mapie-krakowa',
        'only_matching': True,
    }, {
        'url': 'http://teleexpress.tvp.pl/25522307/wierni-wzieli-udzial-w-procesjach',
        'only_matching': True,
    }, {
        'url': 'http://sport.tvp.pl/25522165/krychowiak-uspokaja-w-sprawie-kontuzji-dwa-tygodnie-to-maksimum',
        'only_matching': True,
    }, {
        'url': 'http://www.tvp.info/25511919/trwa-rewolucja-wladza-zdecydowala-sie-na-pogwalcenie-konstytucji',
        'only_matching': True,
    }, {
        'url': 'https://tvp.info/49193823/teczowe-flagi-na-pomnikach-prokuratura-wszczela-postepowanie-wieszwiecej',
        'only_matching': True,
    }, {
        'url': 'https://www.tvpparlament.pl/retransmisje-vod/inne/wizyta-premiera-mateusza-morawieckiego-w-firmie-berotu-sp-z-oo/48857277',
        'only_matching': True,
    }, {
        'url': 'https://tvpworld.com/48583640/tescos-polish-business-bought-by-danish-chain-netto',
        'only_matching': True,
    }, {
        'url': 'https://polandin.com/47942651/pln-10-billion-in-subsidies-transferred-to-companies-pm',
        'only_matching': True,
    }]

    def _parse_vue_website_data(self, webpage, page_id):
        website_data = self._search_regex([
            # website - regiony, tvp.info
            # directory - jp2.tvp.pl
            r'window\s*\.\s*__(?:website|directory)Data\s*=\s*({[\s\S]+?});',
        ], webpage, 'website data')
        if not website_data:
            return None
        return self._parse_json(website_data, page_id, transform_source=js_to_json)

    def _extract_vue_video(self, video_data, page_id=None):
        if isinstance(video_data, compat_str):
            video_data = self._parse_json(video_data, page_id, transform_source=js_to_json)
        video_id = txt_or_none(video_data.get('_id')) or page_id
        if not video_id:
            return
        is_website = video_data.get('type') == 'website'
        if is_website:
            url = video_data['url']
            fucked_up_url_parts = re.match(r'https?://vod\.tvp\.pl/(\d+)/([^/?#]+)', url)
            if fucked_up_url_parts:
                url = 'https://vod.tvp.pl/website/' + ','.join(fucked_up_url_parts.group(2, 1))
        else:
            url = 'tvp:' + video_id
        return {
            '_type': 'url_transparent',
            'id': video_id,
            'url': url,
            'ie_key': (TVPIE if is_website else TVPEmbedIE).ie_key(),
            'title': txt_or_none(video_data.get('title')),
            'description': txt_or_none(video_data.get('lead')),
            'timestamp': int_or_none(video_data.get('release_date_long')),
            'duration': int_or_none(video_data.get('duration')),
            'thumbnails': traverse_obj(video_data, ('image', (None, Ellipsis), 'url'), expected_type=url_or_none) or None,
        }

    def _handle_vuejs_page(self, url, webpage, page_id):
        # vue client-side rendered sites (all regional pages + tvp.info)
        video_data = self._search_regex([
            r'window\.__(?:news|video)Data\s*=\s*({(?:.|\s)+?})\s*;',
        ], webpage, 'video data', default=None)
        if video_data:
            video_data = self._extract_vue_video(video_data, page_id=page_id)
            if video_data:
                return self._extract_vue_video(video_data, page_id=page_id)
        else:
            # paged playlists
            website_data = self._parse_vue_website_data(webpage, page_id)
            if website_data:
                entries = self._vuejs_entries(url, website_data, page_id)

                return {
                    '_type': 'playlist',
                    'id': page_id,
                    'title': txt_or_none(website_data.get('title')),
                    'description': txt_or_none(website_data.get('lead')),
                    'entries': entries,
                }
        raise ExtractorError('Could not extract video/website data')

    def _vuejs_entries(self, url, website_data, page_id):

        def extract_videos(wd):
            for video in traverse_obj(wd, (None, ('latestVideo', (('videos', 'items'), Ellipsis)))):
                video = self._extract_vue_video(video)
                if video:
                    yield video

        for from_ in extract_videos(website_data):
            yield from_

        if website_data.get('items_total_count') > website_data.get('items_per_page'):
            for page in itertools.count(2):
                page_website_data = self._parse_vue_website_data(
                    self._download_webpage(url, page_id, note='Downloading page #%d' % page,
                                           query={'page': page}),
                    page_id)
                if not page_website_data.get('videos') and not page_website_data.get('items'):
                    break
                for from_ in extract_videos(page_website_data):
                    yield from_

    def _real_extract(self, url):
        page_id = self._match_id(url)
        webpage, urlh = self._download_webpage_handle(url, page_id, expected_status=404)

        # The URL may redirect to a VOD
        # example: https://vod.tvp.pl/48463890/wadowickie-spotkania-z-janem-pawlem-ii
        for ie_cls in (TVPVODSeriesIE, TVPVODVideoIE):
            if ie_cls.suitable(urlh.url):
                return self.url_result(urlh.url, ie=ie_cls.ie_key(), video_id=page_id)

        if urlh.getcode() == 404:
            raise compat_HTTPError(url, 404, 'HTTP Error 404: Not Found', urlh.headers, urlh)

        if re.search(
                r'window\s*\.\s*__(?:video|news|website|directory)Data\s*=',
                webpage):
            return self._handle_vuejs_page(url, webpage, page_id)

        # classic server-side rendered sites
        video_id = self._search_regex((
            r'<iframe[^>]+src="[^"]*?embed\.php\?(?:[^&]+&)*ID=(\d+)',
            r'<iframe[^>]+src="[^"]*?object_id=(\d+)',
            r"object_id\s*:\s*'(\d+)'",
            r'data-video-id="(\d+)"',
            # abc.tvp.pl - somehow there are more than one video IDs that seem to be the same video?
            # the first one is referenced to as "copyid", and seems to be unused by the website
            r'<script>\s*tvpabc\.video\.init\(\s*\d+,\s*(\d+)\s*\)\s*</script>',
        ), webpage, 'video id', default=page_id)
        return {
            '_type': 'url_transparent',
            'url': 'tvp:' + video_id,
            'description': self._og_search_description(
                webpage, default=None) or (self._html_search_meta(
                    'description', webpage, default=None)
                    if '//s.tvp.pl/files/portal/v' in webpage else None),
            'thumbnail': self._og_search_thumbnail(webpage, default=None),
            'ie_key': 'TVPEmbed',
        }


class TVPStreamIE(InfoExtractor):
    IE_NAME = 'tvp:stream'
    _VALID_URL = r'(?:tvpstream:|https?://(?:tvpstream\.vod|stream)\.tvp\.pl/(?:\?(?:[^&]+[&;])*channel_id=)?)(?P<id>\d*)'
    _TESTS = [{
        'url': 'https://stream.tvp.pl/?channel_id=56969941',
        'only_matching': True,
    }, {
        'url': 'https://tvpstream.vod.tvp.pl/?channel_id=1455',
        'info_dict': {
            'id': r're:\d+',
            'title': r're:\S.*',
            'ext': 'mp4',
        },
        'params': {
            'skip_download': 'm3u8',
        },
        'add_ie': ['TVPEmbed'],
    }, {
        'url': 'tvpstream:39821455',
        'only_matching': True,
    }, {
        # the default stream when you provide no channel_id, most probably TVP Info
        'url': 'tvpstream:',
        'only_matching': True,
    }, {
        'url': 'https://tvpstream.vod.tvp.pl/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        channel_id = self._match_id(url)
        channel_url = self._proto_relative_url('//stream.tvp.pl/?channel_id=%s' % channel_id or 'default')
        webpage = self._download_webpage(channel_url, channel_id or 'default', 'Downloading channel webpage')
        channels = self._search_json(
            r'window\s*\.\s*__channels\s*=', webpage, 'channel list', channel_id,
            contains_pattern=r'\[\s*\{[\s\S]+}\s*]')
        channel = traverse_obj(channels, (lambda _, v: channel_id == compat_str(v['id'])), get_all=False) if channel_id else channels[0]
        audition = traverse_obj(channel, ('items', lambda _, v: v['is_live'] is True), get_all=False)
        return {
            '_type': 'url_transparent',
            'id': channel_id or channel['id'],
            'url': 'tvp:%s' % (audition['video_id'], ),
            'title': audition.get('title'),
            'alt_title': channel.get('title'),
            'is_live': True,
            'ie_key': 'TVPEmbed',
        }


class TVPEmbedIE(InfoExtractor):
    IE_NAME = 'tvp:embed'
    IE_DESC = 'Telewizja Polska'
    # XFF is not effective
    _GEO_BYPASS = False
    _VALID_URL_PAT = (
        r'''
            (?:
                tvp:
                |https?://
                    (?:[^/]+\.)?
                    (?:tvp(?:parlament)?\.pl|tvp\.info|tvpworld\.com|swipeto\.pl)/
                    (?:sess/
                            (?:tvplayer\.php\?.*?object_id
                            |TVPlayer2/(?:embed|api)\.php\?.*[Ii][Dd])
                        |shared/details\.php\?.*?object_id)
                    =)
            (?P<id>\d+)
        ''')
    _VALID_URL = '(?x)' + _VALID_URL_PAT
    _EMBED_REGEX = [r'(?x)<iframe[^>]+?src=(["\'])(?P<url>{0})'.format(_VALID_URL_PAT)]
    _TESTS = [{
        'url': 'tvp:194536',
        'md5': 'a21eb0aa862f25414430f15fdfb9e76c',
        'info_dict': {
            'id': '194536',
            'ext': 'mp4',
            'title': 'Czas honoru, odc. 13 – Władek',
            'description': 'md5:76649d2014f65c99477be17f23a4dead',
            'age_limit': 12,
            'duration': 2652,
            'series': 'Czas honoru',
            'episode': 'Episode 13',
            'episode_number': 13,
            'season': 'sezon 1',
            'thumbnail': r're:https://.+',
        },
    }, {
        'url': 'http://www.tvp.pl/sess/tvplayer.php?object_id=22670268',
        'md5': '8c9cd59d16edabf39331f93bf8a766c7',
        'info_dict': {
            'id': '22670268',
            'ext': 'mp4',
            'title': 'Panorama, 07.12.2015, 15:40',
        },
        'skip': 'Nie znaleziono obiektu',
    }, {
        'url': 'https://www.tvp.pl/sess/tvplayer.php?object_id=51247504&amp;autoplay=false',
        'info_dict': {
            'id': '51247504',
            'ext': 'mp4',
            'title': 'Razmova 091220',
            'duration': 876,
            'age_limit': 0,
            'thumbnail': r're:https://.+',
        },
    }, {
        # TVPlayer2 embed URL
        'url': 'https://tvp.info/sess/TVPlayer2/embed.php?ID=50595757',
        'only_matching': True,
    }, {
        'url': 'https://wiadomosci.tvp.pl/sess/TVPlayer2/api.php?id=51233452',
        'only_matching': True,
    }, {
        # pulsembed on dziennik.pl
        'url': 'https://www.tvp.pl/shared/details.php?copy_id=52205981&object_id=52204505&autoplay=false&is_muted=false&allowfullscreen=true&template=external-embed/video/iframe-video.html',
        'only_matching': True,
    }, {
        'url': 'tvp:22670268',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        # could be anything that is a valid JS function name
        callback = random.choice((
            'jebac_pis',
            'jebacpis',
            'ziobro',
            'sasin70',
            'sasin_przejebal_70_milionow_PLN',
            'tvp_is_a_state_propaganda_service',
        ))
        webpage = self._download_webpage(
            ('https://www.tvp.pl/sess/TVPlayer2/api.php?id=%s'
             + '&@method=getTvpConfig&@callback=%s') % (video_id, callback), video_id)

        # stripping JSONP padding
        null, datastr = self._search_regex(
            r'\s%s\s*\(\s*(?P<null>null\s*,\s*)?(?P<json>(?(null)\[\s*)?\{(?:[\s\S]+)}(?(null)]\s*))\)\s*;' % (re.escape(callback), ),
            webpage, 'JSON API result', group=('null', 'json'))
        data = self._parse_json(datastr, video_id, fatal=False)
        if null:
            error_desc = traverse_obj(data, (0, 'desc'), expected_type=compat_str)
            if error_desc == 'Obiekt wymaga płatności':
                error_desc = 'Video requires payment and log-in, but log-in is not implemented'
            raise ExtractorError(error_desc or 'unexpected JSON error', expected=error_desc)

        content = data['content']
        info = traverse_obj(content, 'info', expected_type=dict)

        if traverse_obj(info, 'isGeoBlocked', expected_type=bool):
            # actual country list is not provided, we just assume it's always available in PL
            self.raise_geo_restricted(countries=['PL'])

        is_live = traverse_obj(info, 'isLive', expected_type=bool)

        formats = []
        for file in traverse_obj(content, ('files', Ellipsis), expected_type=dict):
            video_url = url_or_none(file.get('url'))
            if not video_url:
                continue
            ext = determine_ext(video_url, None)
            if ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    video_url, video_id, ext='mp4', m3u8_id='hls',
                    fatal=False, live=is_live))
            elif ext == 'mpd':
                if is_live:
                    # doesn't work with either ffmpeg or native downloader
                    continue
                formats.extend(self._extract_mpd_formats(video_url, video_id, mpd_id='dash', fatal=False))
            elif ext == 'f4m':
                formats.extend(self._extract_f4m_formats(video_url, video_id, f4m_id='hds', fatal=False))
            elif video_url.endswith('.ism/manifest'):
                formats.extend(self._extract_ism_formats(video_url, video_id, ism_id='mss', fatal=False))
            elif ext == 'ism':
                if '.ism/manifest' in video_url:
                    formats.extend(self._extract_ism_formats(video_url, video_id, ism_id='mss', fatal=False))
            else:
                # mp4, wmv or something
                quality = traverse_obj(file, 'quality', expected_type=dict) or {}
                formats.append({
                    'format_id': 'direct',
                    'url': video_url,
                    'ext': ext or file.get('type'),
                    'fps': int_or_none(quality.get('fps')),
                    'tbr': int_or_none(quality.get('bitrate'), scale=1000),
                    'width': int_or_none(quality.get('width')),
                    'height': int_or_none(quality.get('height')),
                })

        self._sort_formats(formats)

        title = traverse_obj(info, 'subtitle', 'title', 'seoTitle', expected_type=txt_or_none)
        # `seoDescription` may be Falsen
        description = traverse_obj(info, 'description', 'seoDescription',
                                   expected_type=lambda x: txt_or_none(x or None))
        thumbnails = []
        for thumb in traverse_obj(content, ('posters', Ellipsis), expected_type=dict):
            thumb_url = thumb.get('src')
            if not thumb_url or '{width}' in thumb_url or '{height}' in thumb_url:
                continue
            thumbnails.append({
                'url': thumb.get('src'),
                'width': thumb.get('width'),
                'height': thumb.get('height'),
            })
        age_limit = traverse_obj(info, ('ageGroup', 'minAge'), expected_type=int)
        if age_limit == 1:
            age_limit = 0
        duration = traverse_obj(info, 'duration', expected_type=int) if not is_live else None

        subtitles = {}
        for sub in traverse_obj(content, ('subtitles', Ellipsis), expected_type=dict):
            if not (sub.get('url') and sub.get('lang')):
                continue
            subtitles.setdefault(sub['lang'], []).append({
                'url': sub['url'],
                'ext': sub.get('type'),
            })

        info_dict = {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnails': thumbnails,
            'age_limit': age_limit,
            'is_live': is_live,
            'duration': duration,
            'formats': formats,
            'subtitles': subtitles,
        }

        # vod.tvp.pl
        if traverse_obj(info, 'vortalName') == 'vod':
            info_dict.update({
                'title': '%s, %s' % (info.get('title'), info.get('subtitle')),
                'series': info.get('title'),
                'season': info.get('season'),
                'episode_number': info.get('episode') or None,
            })

        return info_dict


class TVPVODBaseIE(InfoExtractor):
    _API_BASE_URL = 'https://vod.tvp.pl/api/products/'

    def _call_api(self, resource, video_id, **kwargs):
        return self._download_json(
            self._API_BASE_URL + resource, video_id,
            query={'lang': 'pl', 'platform': 'BROWSER'}, **kwargs)

    def _parse_video(self, video):
        video_id = traverse_obj(video, 'externalUid', expected_type=txt_or_none)

        if not video_id:
            return None

        return {
            '_type': 'url',
            'url': 'tvp:' + video_id,
            'ie_key': TVPEmbedIE.ie_key(),
            'title': video.get('title'),
            'description': traverse_obj(video, ('lead', 'description'), expected_type=txt_or_none),
            'age_limit': int_or_none(video.get('rating')),
            'duration': int_or_none(video.get('duration')),
        }


class TVPVODVideoIE(TVPVODBaseIE):
    IE_NAME = 'tvp:vod'
    _VALID_URL = r'https?://vod\.tvp\.pl/[a-z\d-]+,\d+/[a-z\d-]+(?<!-odcinki)(?:-odcinki,\d+/odcinek-\d+,S\d+E\d+)?,(?P<id>\d+)(?:\?[^#]+)?(?:#.+)?$'

    _TESTS = [{
        'url': 'https://vod.tvp.pl/dla-dzieci,24/laboratorium-alchemika-odcinki,309338/odcinek-24,S01E24,311357',
        'info_dict': {
            'id': '60468609',
            'ext': 'mp4',
            'title': 'Laboratorium alchemika, Tusze termiczne. Jak zobaczyć niewidoczne. Odcinek 24',
            'description': 'md5:1d4098d3e537092ccbac1abf49b7cd4c',
            'duration': 300,
            'episode_number': 24,
            'episode': 'Episode 24',
            'age_limit': 0,
            'series': 'Laboratorium alchemika',
            'thumbnail': 're:https://.+',
        },
        'add_ie': ['TVPEmbed'],
    }, {
        'url': 'https://vod.tvp.pl/filmy-dokumentalne,163/ukrainski-sluga-narodu,339667',
        'info_dict': {
            'id': '51640077',
            'ext': 'mp4',
            'title': 'Ukraiński sługa narodu, Ukraiński sługa narodu',
            'series': 'Ukraiński sługa narodu',
            'description': 'md5:b7940c0a8e439b0c81653a986f544ef3',
            'age_limit': 12,
            'duration': 3051,
            'thumbnail': 're:https://.+',
        },
        'add_ie': ['TVPEmbed'],
    }, {
        # new URL format
        'url': 'https://vod.tvp.pl/seriale,18/czas-honoru-odcinki,292065/odcinek-13,S01E13,313867',
        'md5': 'a21eb0aa862f25414430f15fdfb9e76c',
        'info_dict': {
            'id': '194536',
            'ext': 'mp4',
            'title': 'Czas honoru, odc. 13 – Władek',
            'description': 'md5:76649d2014f65c99477be17f23a4dead',
            'age_limit': 12,
        },
        'add_ie': ['TVPEmbed'],
    }, {
        'url': 'https://vod.tvp.pl/filmy-fabularne,136/rozlam,390638',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        video = self._parse_video(
            self._call_api('vods/' + video_id, video_id))
        if not video:
            raise ExtractorError('No video data for ' + video_id)
        return video


class TVPVODSeriesIE(TVPVODBaseIE):
    IE_NAME = 'tvp:vod:series'
    _VALID_URL = r'''(?x)
                    https?://vod\.tvp\.pl/
                        seriale,(?P<cat>\d+)/
                        (?P<display_id>[^,]+?)(?(cat)-odcinki),(?P<id>\d+)
                        (?(cat)|(?P<video>/video)?)(?:[#?]|$)
                '''
    _VALID_URL = r'https?://vod\.tvp\.pl/(?P<display_id>[a-z\d-]+,\d+)/[a-z\d-]+-odcinki,(?P<id>\d+)(?:\?[^#]+)?(?:#.+)?$'

    _TESTS = [{
        # series
        'url': 'https://vod.tvp.pl/seriale,18/ranczo-odcinki,316445',
        #  series (old) - redirects to home page
        #  'url': 'https://vod.tvp.pl/website/wspaniale-stulecie,17069012/video',
        'info_dict': {
            'id': '316445',
            'title': 'Ranczo',
            # 'description': 'md5:a7ccbe1296e6f32425cef17639f1b24b',
            'age_limit': 12,
            'categories': ['seriale'],
        },
        'playlist_mincount': 129,
    }, {
        'url': 'https://vod.tvp.pl/programy,88/rolnik-szuka-zony-odcinki,284514',
        'only_matching': True,
    }, {
        'url': 'https://vod.tvp.pl/dla-dzieci,24/laboratorium-alchemika-odcinki,309338',
        'only_matching': True,
    }]

    def _entries(self, display_id, playlist_id):
        season_path = 'vods/serials/%s/seasons' % (playlist_id, )
        seasons = self._call_api(
            season_path, playlist_id,
            note='Downloading season list') or []

        for ii, season in enumerate(seasons, 1):
            season_id = traverse_obj(season, 'id', expected_type=txt_or_none)
            if not season_id:
                continue
            episodes = self._call_api(
                '%s/%s/episodes' % (season_path, season_id), playlist_id,
                note='Downloading episode list (season %d)' % ii)
            for episode in episodes or []:
                video_id = traverse_obj(episode, 'externalUid', expected_type=txt_or_none)
                if video_id:
                    yield self._parse_video(episode)

    def _real_extract(self, url):
        display_id, playlist_id = self._match_valid_url(url).group('display_id', 'id')
        metadata = self._call_api(
            'vods/serials/' + playlist_id, playlist_id,
            note='Downloading serial metadata') or {}

        pl = self.playlist_result(
            self._entries(display_id, playlist_id), playlist_id, txt_or_none(metadata.get('title')))
        pl.update({
            'description': traverse_obj(metadata, ('description', 'lead'), expected_type=clean_html),
            'categories': traverse_obj(metadata, ('mainCategory', (None, Ellipsis), 'name'), expected_type=txt_or_none),
            'age_limit': traverse_obj(metadata, 'rating', expected_type=int),
        })
        return pl
