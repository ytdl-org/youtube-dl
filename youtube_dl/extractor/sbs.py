# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import (
    compat_kwargs,
    compat_str,
)
from ..utils import (
    HEADRequest,
    float_or_none,
    int_or_none,
    merge_dicts,
    parse_duration,
    parse_iso8601,
    T,
    traverse_obj,
    update_url_query,
    url_or_none,
)


class SBSIE(InfoExtractor):
    IE_DESC = 'sbs.com.au'
    _VALID_URL = r'''(?x)
        https?://(?:www\.)?sbs\.com\.au/(?:
            ondemand(?:
                /video/(?:single/)?|
                /(?:movie|tv-program)/[^/]+/|
                /(?:tv|news)-series/(?:[^/]+/){3}|
                .*?\bplay=|/watch/
            )|news/(?:embeds/)?video/
        )(?P<id>[0-9]+)'''
    _EMBED_REGEX = [r'''(?x)]
            (?:
                <meta\s+property="og:video"\s+content=|
                <iframe[^>]+?src=
            )
            ("|\')(?P<url>https?://(?:www\.)?sbs\.com\.au/ondemand/video/.+?)\1''']

    _TESTS = [{
        # Exceptional unrestricted show for testing, thanks SBS,
        # from an iframe of this page, handled by the generic IE, now 404:
        # http://www.sbs.com.au/thefeed/blog/2014/08/21/dingo-conservation, but replaced by
        # https://www.sbs.com.au/programs/video/320403011771/Dingo-Conservation-The-Feed
        'url': 'http://www.sbs.com.au/ondemand/video/single/320403011771/?source=drupal&vertical=thefeed',
        'md5': 'e49d0290cb4f40d893b8dfe760dce6b0',
        'info_dict': {
            'id': '320403011771',  # formerly '_rFBPRPO4pMR', no longer found
            'ext': 'mp4',
            'title': 'Dingo Conservation (The Feed)',
            'description': 'md5:f250a9856fca50d22dec0b5b8015f8a5',
            'thumbnail': r're:https?://.*\.jpg',
            'duration': 308,
            'timestamp': 1408613220,
            'upload_date': '20140821',
            'uploader': 'SBSC',
            'tags': None,
            'categories': None,
        },
        'expected_warnings': ['Unable to download JSON metadata'],
    }, {
        'url': 'http://www.sbs.com.au/ondemand/video/320403011771/Dingo-Conservation-The-Feed',
        'only_matching': True,
    }, {
        'url': 'http://www.sbs.com.au/news/video/471395907773/The-Feed-July-9',
        'only_matching': True,
    }, {
        'url': 'https://www.sbs.com.au/ondemand/?play=1836638787723',
        'only_matching': True,
    }, {
        'url': 'https://www.sbs.com.au/ondemand/program/inside-windsor-castle?play=1283505731842',
        'only_matching': True,
    }, {
        'url': 'https://www.sbs.com.au/news/embeds/video/1840778819866',
        'only_matching': True,
    }, {
        'url': 'https://www.sbs.com.au/ondemand/watch/1698704451971',
        'only_matching': True,
    }, {
        'url': 'https://www.sbs.com.au/ondemand/movie/coherence/1469404227931',
        'only_matching': True,
    }, {
        'note': 'Live stream',
        'url': 'https://www.sbs.com.au/ondemand/video/1726824003663/sbs-24x7-live-stream-nsw',
        'only_matching': True,
    }, {
        'url': 'https://www.sbs.com.au/ondemand/news-series/dateline/dateline-2022/dateline-s2022-ep26/2072245827515',
        'only_matching': True,
    }, {
        'url': 'https://www.sbs.com.au/ondemand/tv-series/the-handmaids-tale/season-5/the-handmaids-tale-s5-ep1/2065631811776',
        'only_matching': True,
    }, {
        'url': 'https://www.sbs.com.au/ondemand/tv-program/autun-romes-forgotten-sister/2116212803602',
        'only_matching': True,
    }]

    # change default entry_protocol kwarg for _extract_smil_formats()
    # TODO: ..._and_subtitles()
    def _extract_m3u8_formats(self, m3u8_url, video_id, *args, **kwargs):
        # ext, entry_protocol, ...
        entry_protocol = kwargs.get('entry_protocol')
        if not entry_protocol and len(args) <= 1:
            kwargs['entry_protocol'] = 'm3u8_native'
            kwargs = compat_kwargs(kwargs)

        return super(SBSIE, self)._extract_m3u8_formats(m3u8_url, video_id, *args, **kwargs)

    _GEO_COUNTRIES = ['AU']
    # naming for exportability
    AUS_TV_PARENTAL_GUIDELINES = {
        'P': 0,
        'C': 7,
        'G': 0,
        'PG': 0,
        'M': 14,
        'MA15+': 15,
        'AV15+': 15,
        'MAV15+': 15,
        'R18+': 18,
        'NC': 0,  # not classified (unofficial, used by SBS)
    }
    _PLAYER_API = 'https://www.sbs.com.au/api/v3'
    _CATALOGUE_API = 'https://catalogue.pr.sbsod.com/'
    _VOD_BASE_URL = 'https://sbs-vod-prod-01.akamaized.net/'

    def _call_api(self, video_id, path, query=None, data=None, headers=None, fatal=True):
        return self._download_json(update_url_query(
            self._CATALOGUE_API + path, query),
            video_id, headers=headers or {}, fatal=fatal) or {}

    def _get_smil_url(self, video_id):
        return update_url_query(
            self._PLAYER_API + 'video_smil', {'id': video_id})

    def _get_player_data(self, video_id, headers=None, fatal=False):
        return self._download_json(update_url_query(
            self._PLAYER_API + 'video_stream', {'id': video_id, 'context': 'tv'}),
            video_id, headers=headers or {}, fatal=fatal) or {}

    def _real_extract(self, url):
        video_id = self._match_id(url)
        # get media links directly though later metadata may contain contentUrl
        formats, subtitles = self._extract_smil_formats(  # self._extract_smil_formats_and_subtitles(
            self._get_smil_url(video_id), video_id, fatal=False), {}

        if not formats:
            urlh = self._request_webpage(
                HEADRequest(self._VOD_BASE_URL), video_id,
                note='Checking geo-restriction', fatal=False, expected_status=403)
            if urlh:
                error_reasons = urlh.headers.get_all('x-error-reason') or []
                if 'geo-blocked' in error_reasons:
                    self.raise_geo_restricted(countries=self._GEO_COUNTRIES)

        self._sort_formats(formats)

        # try for metadata from the same source
        player_data = self._get_player_data(video_id, fatal=False)
        media = traverse_obj(player_data, 'video_object', T(dict)) or {}

        # get, or add, metadata from catalogue
        media.update(self._call_api(video_id, 'mpx-media/' + video_id, fatal=not media))

        def txt_or_none(s):
            return (s.strip() or None) if isinstance(s, compat_str) else None

        # expected_type fn for thumbs
        def mk_thumb(t):
            u = url_or_none(t.get('contentUrl'))
            return u and {
                'id': t.get('name'),
                'url': u,
                'width': int_or_none(t.get('width')),
                'height': int_or_none(t.get('height')),
            }

        # may be numeric or timecoded
        def really_parse_duration(d):
            result = float_or_none(d)
            if result is None:
                result = parse_duration(d)
            return result

        # For named episodes, use the catalogue's title to set episode, rather than generic 'Episode N'.
        if traverse_obj(media, ('partOfSeries', T(dict))):
            media['epName'] = traverse_obj(media, 'title')

        str = txt_or_none  # instant compat
        return merge_dicts({
            'id': video_id,
        }, traverse_obj(media, {
            'title': ('name', T(str)),
            'description': ('description', T(str)),
            'channel': ('taxonomy', 'channel', 'name', T(str)),
            'series': ((('partOfSeries', 'name'), 'seriesTitle'), T(str)),
            'series_id': ((('partOfSeries', 'uuid'), 'seriesID'), T(str)),
            'season_number': (('partOfSeries', None), 'seasonNumber', T(int_or_none)),
            'episode': ('epName', T(str)),
            'episode_number': ('episodeNumber', T(int_or_none)),
            'timestamp': ('datePublished', ('publication', 'startDate'), T(parse_iso8601)),
            'release_year': ('releaseYear', T(int_or_none)),
            'duration': ('duration', T(really_parse_duration)),
            'is_live': ('liveStream', T(bool)),
            'age_limit': ('classificationID', 'contentRating',
                          T(lambda x: self.AUS_TV_PARENTAL_GUIDELINES.get(x, '').upper() or None)),  # dict.get is unhashable in py3.7
        }, get_all=False), traverse_obj(media, {
            'categories': (('genres', Ellipsis), ('taxonomy', ('genre', 'subgenre'),
                           'name', T(str))),
            'tags': (('consumerAdviceTexts', ('sbsSubCertification', 'consumerAdvice')),
                     Ellipsis, T(str)),
            'thumbnails': ('thumbnails', lambda _, v: v['contentUrl'], T(mk_thumb)),
        }), {
            'formats': formats,
            'subtitles': subtitles,
            'uploader': 'SBSC',
        }, rev=True)
