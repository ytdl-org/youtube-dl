# coding: utf-8
from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor

from .dailymotion import DailymotionIE
from .youtube import YoutubeIE
from ..compat import (
    compat_str as str,
    compat_urllib_parse,
)
from ..utils import (
    clean_html,
    determine_ext,
    extract_attributes,
    ExtractorError,
    filter_dict,
    # format_field,
    HEADRequest,
    int_or_none,
    join_nonempty,
    merge_dicts,
    parse_duration,
    parse_iso8601,
    smuggle_url,
    T,
    traverse_obj,
    unsmuggle_url,
    url_or_none,
)

try:
    if not callable(format_field):
        raise NameError
except NameError:
    from ..utils import IDENTITY, NO_DEFAULT, variadic

    def format_field(obj, field=None, template='%s', ignore=NO_DEFAULT, default='', func=IDENTITY):
        val = traverse_obj(obj, *variadic(field))
        if not (val if ignore is NO_DEFAULT else val in variadic(ignore)):
            return default
        return template % (func(val),)


class FranceTVBaseIE(InfoExtractor):
    @classmethod
    def _make_url_result(cls, video_or_full_id, url=None):
        video_id = video_or_full_id.partition('@')[0]  # for compat with old @catalog IDs
        full_id = 'francetv:%s' % (video_id,)
        if url:
            full_id = smuggle_url(full_id, {
                'hostname': compat_urllib_parse.urlsplit(url).hostname,
            })
        return cls.url_result(full_id, ie=FranceTVIE.ie_key())


class FranceTVIE(InfoExtractor):
    IE_NAME = 'francetv'
    _VALID_URL = r'francetv:(?P<id>[^@#]+)'
    _GEO_COUNTRIES = ['FR']
    _GEO_BYPASS = False

    _TESTS = [{
        # tokenized url is in dinfo['video']['token']
        'url': 'francetv:ec217ecc-0733-48cf-ac06-af1347b849d1',
        'info_dict': {
            'id': 'ec217ecc-0733-48cf-ac06-af1347b849d1',
            'ext': 'mp4',
            'title': '13h15, le dimanche... - Les mystères de Jésus',
            'description': 'md5:75efe8d4c0a8205e5904498ffe1e1a42',
            'timestamp': 1502623500,
            'upload_date': '20170813',
            'duration': 2580,
            'thumbnail': r're:^https?://.*\.jpg$',
        },
        'skip': 'Cette vidéo n\'est malheureusement plus disponible.',
    }, {
        # tokenized url is in dinfo['video']['token']['akamai']
        'url': 'francetv:c5bda21d-2c6f-4470-8849-3d8327adb2ba',
        'info_dict': {
            'id': 'c5bda21d-2c6f-4470-8849-3d8327adb2ba',
            'ext': 'mp4',
            'title': '13h15, le dimanche... - Les mystères de Jésus',
            'description': r're:C\'est dans une église .{145} des décors restaurés que le temps avait effacé\.$',
            'timestamp': 1514118300,
            'upload_date': '20171224',
            'duration': 2880,
            'thumbnail': r're:^https?://.*\.jpg$',
        },
        'skip': 'Cette vidéo n\'est malheureusement plus disponible.',
    }, {
        'url': 'francetv:be492d9f-44c6-4ad0-8356-fb35d7c30e62',
        'info_dict': {
            'id': 'be492d9f-44c6-4ad0-8356-fb35d7c30e62',
            'ext': 'mp4',
            'title': '13h15, le dimanche - Diplomatie : La France face aux empires (épisode 3)',
            'description': r're:Le 29 avril dernier, Donald Trump .{485} doit fixer un nouveau cap, et des valeurs communes\.$',
            'timestamp': 1746965738,
            'upload_date': '20250511',
            'duration': 2948,
            'thumbnail': r're:https?:/(?:/[\w.-]+)+\.jpg$',
        },
        'params': {
            'skip_download': 'needs ffmpeg',
            'format': 'best/bestvideo',
        },
        'expected_warnings': ['hlsnative has detected features it does not support'],
    }, {
        'url': 'francetv:538f8a8a-2c44-11f0-84d6-19616fa871f9',
        'info_dict': {
            'id': '538f8a8a-2c44-11f0-84d6-19616fa871f9',
            'ext': 'mp4',
            'title': 'Angélique Kidjo chante "Imagine" de John Lennon',
            'timestamp': 1746731994,
            'upload_date': '20250508',
            'duration': 226,
            'thumbnail': r're:https?:/(?:/[\w.-]+)+\.jpg$',
        },
        'params': {
            'skip_download': 'needs ffmpeg',
            'format': 'best/bestvideo',
        },
        'expected_warnings': [
            'hlsnative has detected features it does not support',
            'Failed to download (?:MPD manifest|m3u8 information)',
        ],
        'skip': 'geo-restricted to FR',
    }, {
        'url': 'francetv:162311093',
        'only_matching': True,
    }, {
        'url': 'francetv:NI_1004933@Zouzous',
        'only_matching': True,
    }, {
        'url': 'francetv:NI_983319@Info-web',
        'only_matching': True,
    }, {
        'url': 'francetv:NI_983319',
        'only_matching': True,
    }, {
        'url': 'francetv:NI_657393@Regions',
        'only_matching': True,
    }, {
        # france-3 live
        'url': 'francetv:SIM_France3',
        'only_matching': True,
    }]

    def _extract_formats_and_subtitles(self, video_json, video_id):
        formats, subtitles, video_url = [], {}, None

        def maybe_tokenize_video_url(video):
            video_url = video['url']
            format_id = video.get('format')
            token_url = traverse_obj(video, (
                'token', (None, 'akamai'), T(url_or_none)), get_all=False)
            if token_url:
                tokenized_url = self._download_json(
                    token_url, video_id, 'Downloading signed {0} manifest URL'.format(format_id),
                    fatal=False, query={
                        'format': 'json',
                        'url': video_url,
                    })
                video_url = traverse_obj(tokenized_url, (
                    'url', T(url_or_none))) or video_url
            return video_url, format_id

        for video in traverse_obj(video_json, (
                lambda _, v: v.get('url'), {
                    'url': ('url', T(url_or_none)),
                    'format': 'format',
                    'token': 'token',
                }, T(lambda x: x if x['url'] else None))):
            video_url, format_id = maybe_tokenize_video_url(video)

            ext = determine_ext(video_url)
            if ext == 'f4m':
                formats.extend(self._extract_f4m_formats(
                    video_url, video_id, f4m_id=format_id or ext, fatal=False))
            elif ext == 'm3u8':
                format_id = format_id or 'hls'
                # fmts, subs = self._extract_m3u8_formats_and_subtitles(
                fmts, subs = self._extract_m3u8_formats(
                    video_url, video_id, 'mp4', m3u8_id=format_id,
                    entry_protocol='m3u8_native',
                    fatal=False), {}
                for f in traverse_obj(fmts, lambda _, v: (
                        v['vcodec'] == 'none' and v.get('tbr') is None)):
                    tbr = traverse_obj(re.match(
                        r'{0}-[Aa]udio-\w+-(\d+)'.format(format_id),
                        f['format_id']), (1, T(int_or_none)))
                    if tbr is not None:
                        f.update({
                            'tbr': tbr,
                            'acodec': 'mp4a',
                        })
                formats.extend(fmts)
                self._merge_subtitles(subs, target=subtitles)
            elif ext == 'mpd':
                fmts, subs = self._extract_mpd_formats_and_subtitles(
                    video_url, video_id, mpd_id=format_id or 'dash', fatal=False)
                formats.extend(fmts)
                self._merge_subtitles(subs, target=subtitles)
            elif video_url.startswith('rtmp'):
                formats.append({
                    'url': video_url,
                    'format_id': join_nonempty('rtmp', format_id),
                    'ext': 'flv',
                })
            else:
                if self._is_valid_url(video_url, video_id, format_id):
                    formats.append({
                        'url': video_url,
                        'format_id': format_id,
                    })

            # XXX: what is video['captions']?

        if not formats and video_url:
            urlh = self._request_webpage(
                HEADRequest(video_url), video_id, 'Checking for geo-restriction',
                fatal=False, expected_status=403)
            if urlh and urlh.headers.get('x-errortype') == 'geo':
                self.raise_geo_restricted(countries=self._GEO_COUNTRIES)  # , metadata_available=True)

        self._sort_formats(formats, field_preference=('res', 'tbr', 'proto'))

        for f in formats:
            if f.get('acodec') != 'none' and f.get('language') in ('qtz', 'qad'):
                f['language_preference'] = -10
                f['format_note'] = 'audio description{0}'.format(format_field(f, 'format_note', ', %s'))

        return formats, subtitles

    def _extract_video(self, video_id, hostname=None):
        videos = []
        info = {'id': video_id}
        drm_formats = False

        # desktop+chrome returns dash; mobile+safari returns hls
        for device_type, browser in [('desktop', 'chrome'), ('mobile', 'safari')]:
            dinfo = self._download_json(
                'https://k7.ftven.fr/videos/{0}'.format(video_id), video_id,
                'Downloading {0} {1} video JSON'.format(device_type, browser), query=filter_dict({
                    'device_type': device_type,
                    'browser': browser,
                    'domain': hostname,
                }), fatal=False, expected_status=422)  # 422 json gives detailed error code/message

            if not dinfo:
                continue

            video = traverse_obj(dinfo, ('video', T(dict)))
            code = traverse_obj(dinfo, ('code', T(int_or_none)))
            if video:
                videos.append(video)
                info = merge_dicts(info, traverse_obj(video, {
                    'duration': 'duration',
                    'is_live': 'is_live',
                }))
            elif code:
                if code == 2009:
                    self.raise_geo_restricted(countries=self._GEO_COUNTRIES)
                elif code in (2015, 2017):
                    # 2015: L'accès à cette vidéo est impossible. (DRM-only)
                    # 2017: Cette vidéo n'est pas disponible depuis le site web mobile (b/c DRM)
                    drm_formats = True
                    continue
                elif code == 2007:
                    # 2007: Ce direct est terminé.
                    raise ExtractorError(
                        'Live broadcast has ended; video unavailable.',
                        video_id=video_id, expected=True)
                self.report_warning('{0} said: "({1}) {2}"'.format(
                    self.IE_NAME, code, clean_html(dinfo.get('message'))))
                continue

            # avoid duplicating title text
            titles = ('title', 'additional_title')
            title_parts = [
                re.sub(r'(?:_|[^\w])+', ' ', t).strip()
                for t in traverse_obj(dinfo, ('meta', titles))]
            if len(title_parts) == 2 and title_parts[0] == title_parts[1]:
                titles = titles[:1]

            info = merge_dicts(info, traverse_obj(dinfo, ('meta', {
                'title': T(lambda d: join_nonempty(
                    *((d.get(t) or '').strip() or None
                      for t in titles), delim=' - ')),
                'description': ('description', T(lambda s: s.strip() or None)),
                'thumbnail': ('image_url', T(url_or_none)),
                'timestamp': ('broadcasted_at', T(parse_iso8601)),
                'duration': ('playtime', T(parse_duration)),
                'alt_title': 'additional_title',
            })), traverse_obj(dinfo, (
                # meta['pre_title'] contains season and episode number for series in format "S<ID> E<ID>"
                'meta', 'pre_title', T(lambda x: re.search(
                    r'S(\d+)\s*E(\d+)', x)), {
                        'season_number': (1, T(int_or_none)),
                        'episode_number': (2, T(int_or_none)),
                })))

        if not videos and drm_formats:
            self.report_drm(video_id)

        formats, subtitles = self._extract_formats_and_subtitles(videos, video_id)

        if info.get('is_live'):
            info['title'] = self._live_title(info['title'])

        return merge_dicts(info, {
            'formats': formats,
            'subtitles': subtitles,
            # '_format_sort_fields': ('res', 'tbr', 'proto'),  # prioritize m3u8 over dash
        }, {
            'episode': info.get('alt_title'),
            'series': info['title'],
        } if info.get('episode_number') else {})

    def _real_extract(self, url):
        url, smuggled_data = unsmuggle_url(url, {})
        video_id = self._match_id(url)
        hostname = smuggled_data.get('hostname') or 'www.france.tv'

        return self._extract_video(video_id, hostname=hostname)


class FranceTVEmbedIE(FranceTVBaseIE):
    _VALID_URL = r'''(?x)
        https?://embed\.francetv\.fr(?:/?\?(?:.*&)?(?P<ue>ue)=|/)
        # Say (?:|...) instead of (?:...)? when ... ends .* to avoid
        # python/cpython#62847 (fixed from at least 3.5 and late 2.7)
        (?P<id>[\da-f]{32})(?:|(?(ue)&|/?[?#]).*)$
    '''
    _TESTS = [{
        'url': 'http://embed.francetv.fr/?ue=7fd581a2ccf59d2fc5719c5c13cf6961',
        'add_ie': [FranceTVIE.ie_key()],
        'info_dict': {
            'id': 'NI_983319',
            'ext': 'mp4',
            'title': 'Le Pen Reims',
            'upload_date': '20170505',
            'timestamp': 1493981780,
            'duration': 16,
        },
        'params': {
            'skip_download': True,
        },
        'skip': 'Gone',
    }, {
        'url': 'https://embed.francetv.fr/ecc238d6df70c0e9d76972fe1890a0e5',
        'add_ie': [FranceTVIE.ie_key()],
        'info_dict': {
            'id': '41495932-eaa9-11ef-a8a1-57a09c50f7ce',
            'ext': 'mp4',
            'title': 'Pouvoir d’achat : les Français de plus en plus endettés - Émission du jeudi 13 février 2025',
            'timestamp': 1739484973,
            'upload_date': '20250213',
            'duration': 111,
            'thumbnail': r're:https?://[\w.]+\.fr(?:/[\w-]+)+\.jpg$',
        },
        'params': {
            'format': 'best/bestvideo',
            'skip_download': 'm3u8',
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        video = self._download_json(
            'https://api-embed.webservices.francetelevisions.fr/v2/key/%s' % (video_id,),
            video_id)

        return self._make_url_result(video['video_id'], video.get('url_source'))


class FranceTVSiteIE(FranceTVBaseIE):
    IE_NAME = 'francetv:site'
    _VALID_URL = r'https?://(?:(?:www|mobile)\.)?france\.tv/(?:[^/]+/)*(?P<id>[^/]+)\.html'

    _TESTS = [{
        'url': 'https://www.france.tv/france-2/13h15-le-dimanche/140921-les-mysteres-de-jesus.html',
        'info_dict': {
            'id': 'ec217ecc-0733-48cf-ac06-af1347b849d1',  # old: c5bda21d-2c6f-4470-8849-3d8327adb2ba'
            'ext': 'mp4',
            'title': '13h15, le dimanche... - Les mystères de Jésus',
            'description': 'md5:75efe8d4c0a8205e5904498ffe1e1a42',
            'timestamp': 1502623500,
            'duration': 2580,
            'thumbnail': r're:ttps?://.*\.jpg$',
            'upload_date': '20170813',
        },
        'skip': 'La vidéo n\'est pas disponible',
    }, {
        'url': 'https://www.france.tv/france-2/diplomatie/7129460-la-france-face-aux-empires.html',
        'add_ie': [FranceTVIE.ie_key()],
        'info_dict': {
            'id': 'be492d9f-44c6-4ad0-8356-fb35d7c30e62',
            'ext': 'mp4',
            'title': '13h15, le dimanche - Diplomatie : La France face aux empires (épisode 3)',
            'description': r're:Le 29 avril dernier, Donald Trump .{485} doit fixer un nouveau cap, et des valeurs communes\.$',
            'timestamp': 1746965738,
            'upload_date': '20250511',
            'duration': 2948,
            'thumbnail': r're:https?:/(?:/[\w.-]+)+\.jpg$',
        },
        'params': {
            'skip_download': 'needs ffmpeg',
            'format': 'best/bestvideo',
        },
        'expected_warnings': ['hlsnative has detected features it does not support'],
    }, {
        # geo-restricted
        'url': 'https://www.france.tv/enfants/six-huit-ans/foot2rue/saison-1/3066387-duel-au-vieux-port.html',
        'info_dict': {
            'id': 'a9050959-eedd-4b4a-9b0d-de6eeaa73e44',
            'ext': 'mp4',
            'title': 'Foot2Rue - Duel au vieux port',
            'episode': 'Duel au vieux port',
            'series': 'Foot2Rue',
            'episode_number': 1,
            'season_number': 1,
            'timestamp': 1642761360,
            'upload_date': '20220121',
            'season': 'Season 1',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 1441,
        },
        'skip': 'La vidéo n\'est pas disponible',
    }, {
        # geo-restricted
        'url': 'https://www.france.tv/spectacles-et-culture/musique-pop-rock-electro/7170893-angelique-kidjo-chante-imagine-de-john-lennon.html',
        'add_ie': [FranceTVIE.ie_key()],
        'info_dict': {
            'id': '538f8a8a-2c44-11f0-84d6-19616fa871f9',
            'ext': 'mp4',
            'title': 'Angélique Kidjo chante "Imagine" de John Lennon',
            'timestamp': 1746731994,
            'upload_date': '20250508',
            'duration': 226,
            'thumbnail': r're:https?:/(?:/[\w.-]+)+\.jpg$',
        },
        'expected_warnings': [
            'hlsnative has detected features it does not support',
            'Failed to download (?:MPD manifest|m3u8 information)',
        ],
        'skip': 'Geo-restricted to FR',
    }, {
        # geo-restricted livestream (workflow == 'token-akamai')
        'url': 'https://www.france.tv/france-4/direct.html',
        'info_dict': {
            'id': '9a6a7670-dde9-4264-adbc-55b89558594b',
            'ext': 'mp4',
            'title': r're:France 4 en direct .+',
            'live_status': 'is_live',
        },
        'skip': 'geo-restricted livestream',
    }, {
        # livestream (workflow == 'dai')
        'url': 'https://www.france.tv/france-2/direct.html',
        'add_ie': [FranceTVIE.ie_key()],
        'info_dict': {
            'id': '006194ea-117d-4bcf-94a9-153d999c59ae',
            'ext': 'mp4',
            'title': r're:France 2 en direct \d{4}-[01]\d-[0-3]\d [0-2]\d:[0-5]\d$',
            # 'live_status': 'is_live',
            'is_live': True,
        },
        'params': {'skip_download': 'livestream', 'format': 'best/bestvideo'},
    }, {
        # france3
        'url': 'https://www.france.tv/france-3/des-chiffres-et-des-lettres/139063-emission-du-mardi-9-mai-2017.html',
        'only_matching': True,
    }, {
        # france4
        'url': 'https://www.france.tv/france-4/hero-corp/saison-1/134151-apres-le-calme.html',
        'only_matching': True,
    }, {
        # france5
        'url': 'https://www.france.tv/france-5/c-a-dire/saison-10/137013-c-a-dire.html',
        'only_matching': True,
    }, {
        # franceo
        'url': 'https://www.france.tv/france-o/archipels/132249-mon-ancetre-l-esclave.html',
        'only_matching': True,
    }, {
        'url': 'https://www.france.tv/documentaires/histoire/136517-argentine-les-500-bebes-voles-de-la-dictature.html',
        'only_matching': True,
    }, {
        'url': 'https://www.france.tv/jeux-et-divertissements/divertissements/133965-le-web-contre-attaque.html',
        'only_matching': True,
    }, {
        'url': 'https://mobile.france.tv/france-5/c-dans-l-air/137347-emission-du-vendredi-12-mai-2017.html',
        'only_matching': True,
    }, {
        'url': 'https://www.france.tv/142749-rouge-sang.html',
        'only_matching': True,
    }, {
        # france-3 live
        'url': 'https://www.france.tv/france-3/direct.html',
        'only_matching': True,
    }]

    def _search_nextjs_data_new(self, html, video_id, paths, **kwargs):

        def find_json(s):
            return self._search_json(
                r'\w+\s*:\s*', s, 'next js data', video_id, contains_pattern=r'\[([\s\S]+)\]', default=None)

        def yield_nextjs_data(html):
            for m in re.finditer(r'<script\b[^>]*>\s*self\.__next_f\.push\(\s*(\[.+?\])\s*\);?\s*</script>', html):
                for from_ in traverse_obj(m, (
                        1, T(json.loads),
                        Ellipsis, T(find_json), Ellipsis)):
                    yield from_

        return traverse_obj(yield_nextjs_data(html), (Ellipsis,) + paths, **kwargs)

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        E = Ellipsis  # abbreviation
        nextjs_data = self._search_nextjs_data_new(
            webpage, display_id, (
                'children', E, E,
                'children', E, E, 'children'))

        if traverse_obj(nextjs_data, (E, E, 'children', E, 'isLive', T(bool)),
                        get_all=False):
            # For livestreams we need the id of the stream instead of the currently airing episode id
            video_id = traverse_obj(nextjs_data, (
                E, E, (None,
                       ('children', E, 'children', E, 'children', E, 'children',
                        E, E, 'children', E, E, 'children', E, E, 'children')),
                (E, (E, E)), 'options', 'id', T(str)), get_all=False)
        else:
            video_id = traverse_obj(nextjs_data, (
                E, E, E, 'children',
                lambda _, v: v['video']['url'] == compat_urllib_parse.urlparse(url).path,
                'video', ('playerReplayId', 'siId'), T(str)), get_all=False)

        if not video_id:
            raise ExtractorError('Unable to extract video ID')

        return self._make_url_result(video_id, url)


class FranceTVInfoIE(FranceTVBaseIE):
    # new domain w/o `tv` as of 2025-05-14
    IE_NAME = 'franceinfo.fr'
    _VALID_URL = r'https?://(?:www|mobile|france3-regions|la1ere)\.franceinfo\.fr/(?:[^/]+/)*(?P<id>[^/?#&.]+)'
    _TESTS = [{
        'url': 'https://www.franceinfo.fr/replay-jt/france-3/soir-3/jt-grand-soir-3-jeudi-22-aout-2019_3561461.html',
        'add_ie': [FranceTVIE.ie_key()],
        'info_dict': {
            'id': 'd12458ee-5062-48fe-bfdd-a30d6a01b793',
            'ext': 'mp4',
            'title': 'Soir 3 - Émission du jeudi 22 août 2019',
            'description': 'Une heure d\'informations proposée par la rédaction nationale de la chaîne, avec des reportages, des débats, des invités et des chroniques.',
            'timestamp': 1566510730,
            'upload_date': '20190822',
            'thumbnail': r're:^https?://.*\.jpe?g$',
            'duration': 1637,
            'subtitles': {
                # TODO: 'fr': 'mincount:2',
            },
        },
        'params': {
            'format': 'best/bestvideo',
            'skip_download': True,
        },
    }, {
        'note': 'Only an image exists in initial webpage instead of the video',
        'url': 'https://www.franceinfo.fr/sante/maladie/coronavirus/covid-19-en-inde-une-situation-catastrophique-a-new-dehli_4381095.html',
        'add_ie': [FranceTVIE.ie_key()],
        'info_dict': {
            'id': '7d204c9e-a2d3-11eb-9e4c-000d3a23d482',
            'ext': 'mp4',
            'title': 'Covid-19 : une situation catastrophique à New Dehli - Édition du mercredi 21 avril 2021',
            'timestamp': 1619028518,
            'upload_date': '20210421',
            'thumbnail': r're:^https?://.*\.jpe?g$',
            'duration': 76,
        },
        'params': {
            'format': 'best/bestvideo',
            'skip_download': True,
        },
    }, {
        'url': 'https://la1ere.franceinfo.fr/martinique/programme-video/diffusion/4774522-origine-kongo.html',
        'add_ie': [FranceTVIE.ie_key()],
        'info_dict': {
            'id': '97790f3a-b23a-4004-bd9c-b89fde6f95bf',
            'ext': 'mp4',
            'title': 'Origine : Kongo',
            'timestamp': 1679680110,
            'upload_date': '20230424',
            'duration': 3146,
            'thumbnail': r're:https?:/(?:/[\w.-]+)+\.jpg$',
        },
        'params': {
            'format': 'best/bestvideo',
            'skip_download': True,
        },
        'skip': 'Geo-restricted to FR',
    }, {
        'url': 'https://la1ere.franceinfo.fr/guadeloupe/programme-video/la1ere_guadeloupe_le-13h-en-guadeloupe/diffusion/5643549-emission-du-lundi-29-janvier-2024.html',
        'add_ie': [FranceTVIE.ie_key()],
        'info_dict': {
            'id': r're:[\w-]{35}',
            'ext': 'mp4',
            'title': 'Le 13H en Guadeloupe - Émission du lundi 29 janvier 2025',
            'description': 'Le 13h en Guadeloupe une édition avec la vocation de l\'hyper-proximité. Nos journalistes sur le terrain "duplex-interactivité-nouveaux systèmes d\'informations" une nouvelle écriture de l\'info',
            'timestamp': int,
            'upload_date': '20240129',
            'thumbnail': r're:^https?://.*\.png$',
            'duration': 1606,
        },
        'params': {
            'format': 'best/bestvideo',
            'skip_download': True,
        },
        'skip': 'expired?',
    }, {
        'url': 'https://la1ere.franceinfo.fr/guadeloupe/programme-video/la1ere_guadeloupe_le-13h-en-guadeloupe/diffusion/7151885-emission-du-lundi-12-mai-2025.html',
        'add_ie': [FranceTVIE.ie_key()],
        'info_dict': {
            'id': '7044dc7a-45d1-4dd0-b2a9-21ee31ec4e8c',
            'ext': 'mp4',
            'title': 'Le 13H en Guadeloupe - Émission du lundi 12 mai 2025',
            'description': 'Le 13h en Guadeloupe une édition avec la vocation de l\'hyper-proximité. Nos journalistes sur le terrain "duplex-interactivité-nouveaux systèmes d\'informations" une nouvelle écriture de l\'info',
            'timestamp': 1747069200,
            'upload_date': '20250512',
            'thumbnail': r're:^https?://.*\.png$',
            'duration': 1537,
        },
        'params': {
            'format': 'best/bestvideo',
            'skip_download': 'm3u8',
        },
    }, {
        'url': 'http://www.franceinfo.fr/elections/europeennes/direct-europeennes-regardez-le-debat-entre-les-candidats-a-la-presidence-de-la-commission_600639.html',
        'only_matching': True,
    }, {
        'url': 'http://www.franceinfo.fr/economie/entreprises/les-entreprises-familiales-le-secret-de-la-reussite_933271.html',
        'only_matching': True,
    }, {
        'url': 'http://france3-regions.franceinfo.fr/bretagne/cotes-d-armor/thalassa-echappee-breizh-ce-venredi-dans-les-cotes-d-armor-954961.html',
        'only_matching': True,
    }, {
        # Dailymotion embed
        'url': 'http://www.franceinfo.fr/politique/notre-dame-des-landes/video-sur-france-inter-cecile-duflot-denonce-le-regard-meprisant-de-patrick-cohen_1520091.html',
        'add_ie': ['Dailymotion'],
        'md5': '95550b6e6802c4c81d4b5b41fb84c691',
        'info_dict': {
            'id': 'x4iiko0',
            'ext': 'mp4',
            'title': 'NDDL, référendum, Brexit : Cécile Duflot répond à Patrick Cohen',
            'description': 'Au lendemain de la victoire du "oui" au référendum sur l\'aéroport de Notre-Dame-des-Landes, l\'ancienne ministre écologiste est l\'invitée de Patrick Cohen. Plus d\'info : https://www.franceinter.fr/emissions/le-7-9/le-7-9-27-juin-2016',
            'timestamp': 1467011958,
            'upload_date': '20160627',
            'uploader': 'France Inter',
            'uploader_id': 'x2q2ez',
            'view_count': int,
            'tags': ['Politique', 'France Inter', '27 juin 2016', 'Linvité de 8h20', 'Cécile Duflot', 'Patrick Cohen'],
            'age_limit': 0,
            'duration': 640,
            'like_count': int,
            'thumbnail': r're:https://[^/?#]+/v/[^/?#]+/x1080',
        },
    }, {
        'url': 'http://france3-regions.franceinfo.fr/limousin/emissions/jt-1213-limousin',
        'only_matching': True,
    }, {
        # "<figure id=" pattern (#28792)
        'url': 'https://www.franceinfo.fr/culture/patrimoine/incendie-de-notre-dame-de-paris/notre-dame-de-paris-de-l-incendie-de-la-cathedrale-a-sa-reconstruction_4372291.html',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        def get_embed_entries(ie):
            urls = ie._extract_urls(webpage)
            if urls:
                return [self.url_result(embed_url, ie.ie_key())
                        for embed_url in urls]

        dailymotion_entries = get_embed_entries(DailymotionIE)
        if dailymotion_entries:
            return self.playlist_result(dailymotion_entries, display_id)

        result = {}
        player_button = extract_attributes(self._search_regex(
            r'(<button\s[^>]*(?<!-)\bdata-url\s*=\s*["\'][^>]{2,}>)',
            webpage, 'fi player button', default=''))
        if player_button.get('data-url'):
            result = merge_dicts(traverse_obj(player_button, {
                'id': 'data-expression-uuid',
                'timestamp': ('data-start-time', T(int_or_none)),
                'duration': T(lambda x: int(x['data-end-time']) - int(x['data-start-time'])),
                'title': 'data-extract-title',
                'description': 'data-diffusion-title',
                'series': 'data-emission-title',
                'url': ('data-url', T(url_or_none)),
            }), {
                'thumbnail': self._og_search_thumbnail(webpage, default=None),
            })
            if result.get('url'):
                if not result.get('title'):
                    result['title'] = self._html_search_regex(
                        r'''Retrouvez l'intégralité du\s+(.+)\s*:''',
                        webpage, 'Alt title').replace('"', '')

        if not result.get('id'):
            result['id'] = (
                extract_attributes(self._search_regex(
                    r'(<button\s[^>]*(?<!-)\bdata-cy\s*=\s*("|\')francetv-player-wrapper\2[^>]*>)',
                    webpage, 'player button', default='')).get('id')
                or self._search_regex((
                    r'player\.load[^;]+src:\s*["\']([^"\']+)',
                    r'id-video=([^@]+@[^"]+)',
                    r'<a[^>]+href="(?:https?:)?//videos\.francetv\.fr/video/([^@]+@[^"]+)"',
                    r'''(?x)(?:
                        (?:(?:(?<!-)\bdata-(?:expression-uu)?id|<figure[^>]+\bid)=["'])|
                        (?<!-)\bdata-piano="\{.[\s\S]*?&quot;video_factory_id&quot;:&quot;)
                        ([\da-f]{8}(?:-[\da-f]{4}){3}-[\da-f]{12})
                    '''), webpage, 'video id')
            )

        if result.get('url'):
            yt_entries = get_embed_entries(YoutubeIE)
            return self.playlist_result(
                [result] + yt_entries, display_id) if yt_entries else result

        return self._make_url_result(result['id'], url)


class FranceTVInfoSportIE(FranceTVBaseIE):
    # now URLs redirect to franceinfo.fr, with /sports prepended if not present
    IE_NAME = 'sport.francetvinfo.fr'
    _VALID_URL = r'https?://sport\.francetvinfo\.fr/(?:[^/]+/)*(?P<id>[^/?#&]+)'
    _TESTS = [{
        'url': 'https://sport.francetvinfo.fr/les-jeux-olympiques/retour-sur-les-meilleurs-moments-de-pyeongchang-2018',
        'info_dict': {
            'id': '6e49080e-3f45-11e8-b459-000d3a2439ea',
            'ext': 'mp4',
            'title': 'Retour sur les meilleurs moments de Pyeongchang 2018',
            'timestamp': 1523639962,
            'upload_date': '20180413',
        },
        'params': {
            'skip_download': True,
        },
        'add_ie': [FranceTVIE.ie_key(), 'Generic'],
        'skip': '404 La page que vous souhaitiez voir est inaccessible.',
    }]

    def _real_extract(self, url):
        return self.url_result(smuggle_url(url, {'to_generic': True}), 'Generic')


class GenerationWhatIE(InfoExtractor):
    _WORKING = False
    # obsolete site: redirection to https://www.francetelevisions.fr/et-vous/le-lab
    IE_NAME = 'france2.fr:generation-what'
    _VALID_URL = r'https?://generation-what\.francetv\.fr/[^/]+/video/(?P<id>[^/?#&]+)'

    _TESTS = [{
        'url': 'http://generation-what.francetv.fr/portrait/video/present-arms',
        'info_dict': {
            'id': 'wtvKYUG45iw',
            'ext': 'mp4',
            'title': 'Generation What - Garde à vous - FRA',
            'uploader': 'Generation What',
            'uploader_id': 'UCHH9p1eetWCgt4kXBYCb3_w',
            'upload_date': '20160411',
        },
        'params': {
            'skip_download': True,
        },
        'add_ie': ['Youtube'],
    }, {
        'url': 'http://generation-what.francetv.fr/europe/video/present-arms',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        youtube_id = self._search_regex(
            r"window\.videoURL\s*=\s*'([0-9A-Za-z_-]{11})';",
            webpage, 'youtube id')

        return self.url_result(youtube_id, ie='Youtube', video_id=youtube_id)


class CultureboxIE(FranceTVBaseIE):
    # obsolete site: redirects to www.france.tv/spectacles-et-culture/
    # specific URLs redirect under www.france.tv, eg /france-2/...
    _VALID_URL = r'https?://(?:m\.)?culturebox\.francetvinfo\.fr/(?:[^/]+/)*(?P<id>[^/?#&]+)'

    _TESTS = [{
        'url': 'https://culturebox.francetvinfo.fr/opera-classique/musique-classique/c-est-baroque/concerts/cantates-bwv-4-106-et-131-de-bach-par-raphael-pichon-57-268689',
        'info_dict': {
            'id': 'EV_134885',
            'ext': 'mp4',
            'title': 'Cantates BWV 4, 106 et 131 de Bach par Raphaël Pichon 5/7',
            'description': 'md5:19c44af004b88219f4daa50fa9a351d4',
            'upload_date': '20180206',
            'timestamp': 1517945220,
            'duration': 5981,
        },
        'params': {
            'skip_download': True,
        },
        'add_ie': [FranceTVIE.ie_key(), 'Generic'],
    }]

    def _real_extract(self, url):
        return self.url_result(smuggle_url(url, {'to_generic': True}), 'Generic')


class FranceTVJeunesseIE(FranceTVBaseIE):
    # obsolete site: redirection to https://www.france.tv/enfants/
    _WORKING = False
    _VALID_URL = r'(?P<url>https?://(?:www\.)?(?:zouzous|ludo)\.fr/heros/(?P<id>[^/?#&]+))'

    _TESTS = [{
        'url': 'https://www.zouzous.fr/heros/simon',
        'info_dict': {
            'id': 'simon',
        },
        'playlist_count': 9,
    }, {
        'url': 'https://www.ludo.fr/heros/ninjago',
        'info_dict': {
            'id': 'ninjago',
        },
        'playlist_count': 10,
    }, {
        'url': 'https://www.zouzous.fr/heros/simon?abc',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        playlist_id = mobj.group('id')

        playlist = self._download_json(
            '%s/%s' % (mobj.group('url'), 'playlist'), playlist_id)

        if not playlist.get('count'):
            raise ExtractorError(
                '%s is not available' % playlist_id, expected=True)

        entries = []
        for item in playlist['items']:
            identity = item.get('identity')
            if identity and isinstance(identity, str):
                entries.append(self._make_url_result(identity))

        return self.playlist_result(entries, playlist_id)
