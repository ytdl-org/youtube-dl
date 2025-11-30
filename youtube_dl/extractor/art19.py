# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    float_or_none,
    int_or_none,
    merge_dicts,
    parse_iso8601,
    str_or_none,
    T,
    traverse_obj,
    url_or_none,
)


class Art19IE(InfoExtractor):
    _UUID_REGEX = r'[\da-f]{8}-?[\da-f]{4}-?[\da-f]{4}-?[\da-f]{4}-?[\da-f]{12}'
    _VALID_URL = (
        r'https?://(?:www\.)?art19\.com/shows/[^/#?]+/episodes/(?P<id>{0})'.format(_UUID_REGEX),
        r'https?://rss\.art19\.com/episodes/(?P<id>{0})\.mp3'.format(_UUID_REGEX),
    )
    _EMBED_REGEX = (r'<iframe\b[^>]+\bsrc\s*=\s*[\'"](?P<url>{0})'.format(_VALID_URL[0]),)

    _TESTS = [{
        'url': 'https://rss.art19.com/episodes/5ba1413c-48b8-472b-9cc3-cfd952340bdb.mp3',
        'info_dict': {
            'id': '5ba1413c-48b8-472b-9cc3-cfd952340bdb',
            'ext': 'mp3',
            'title': 'Why Did DeSantis Drop Out?',
            'series': 'The Daily Briefing',
            'release_timestamp': 1705941275,
            'description': 'md5:da38961da4a3f7e419471365e3c6b49f',
            'episode': 'Episode 582',
            'thumbnail': r're:^https?://content\.production\.cdn\.art19\.com.*\.jpeg$',
            'series_id': 'ed52a0ab-08b1-4def-8afc-549e4d93296d',
            'upload_date': '20240122',
            'timestamp': 1705940815,
            'episode_number': 582,
            # 'modified_date': '20240122',
            'episode_id': '5ba1413c-48b8-472b-9cc3-cfd952340bdb',
            'modified_timestamp': int,
            'release_date': '20240122',
            'duration': 527.4,
        },
    }, {
        'url': 'https://art19.com/shows/scamfluencers/episodes/8319b776-4153-4d22-8630-631f204a03dd',
        'info_dict': {
            'id': '8319b776-4153-4d22-8630-631f204a03dd',
            'ext': 'mp3',
            'title': 'Martha Stewart: The Homemaker Hustler Part 2',
            # 'modified_date': '20240116',
            'upload_date': '20240105',
            'modified_timestamp': int,
            'episode_id': '8319b776-4153-4d22-8630-631f204a03dd',
            'series_id': 'd3c9b8ca-26b3-42f4-9bd8-21d1a9031e75',
            'thumbnail': r're:^https?://content\.production\.cdn\.art19\.com.*\.jpeg$',
            'description': r're:(?s)In the summer of 2003, Martha Stewart is indicted .{695}#do-not-sell-my-info\.$',
            'release_timestamp': 1705305660,
            'release_date': '20240115',
            'timestamp': 1704481536,
            'episode_number': 88,
            'series': 'Scamfluencers',
            'duration': 2588.37501,
            'episode': 'Episode 88',
        },
    }]
    _WEBPAGE_TESTS = [{
        'url': 'https://www.nu.nl/formule-1/6291456/verstappen-wordt-een-synoniem-voor-formule-1.html',
        'info_dict': {
            'id': '7d42626a-7301-47db-bb8a-3b6f054d77d7',
            'ext': 'mp3',
            'title': "'Verstappen wordt een synoniem voor Formule 1'",
            'season': 'Seizoen 6',
            'description': 'md5:39a7159a31c4cda312b2e893bdd5c071',
            'episode_id': '7d42626a-7301-47db-bb8a-3b6f054d77d7',
            'duration': 3061.82111,
            'series_id': '93f4e113-2a60-4609-a564-755058fa40d8',
            'release_date': '20231126',
            'modified_timestamp': 1701156004,
            'thumbnail': r're:^https?://content\.production\.cdn\.art19\.com.*\.jpeg$',
            'season_number': 6,
            'episode_number': 52,
            # 'modified_date': '20231128',
            'upload_date': '20231126',
            'timestamp': 1701025981,
            'season_id': '36097c1e-7455-490d-a2fe-e2f10b4d5f26',
            'series': 'De Boordradio',
            'release_timestamp': 1701026308,
            'episode': 'Episode 52',
        },
    }, {
        'url': 'https://www.wishtv.com/podcast-episode/larry-bucshon-announces-retirement-from-congress/',
        'info_dict': {
            'id': '8da368bd-08d1-46d0-afaa-c134a4af7dc0',
            'ext': 'mp3',
            'title': 'Larry Bucshon announces retirement from congress',
            'upload_date': '20240115',
            'episode_number': 148,
            'episode': 'Episode 148',
            'thumbnail': r're:^https?://content\.production\.cdn\.art19\.com.*\.jpeg$',
            'release_date': '20240115',
            'timestamp': 1705328205,
            'release_timestamp': 1705329275,
            'series': 'All INdiana Politics',
            # 'modified_date': '20240117',
            'modified_timestamp': 1705458901,
            'series_id': 'c4af6c27-b10f-4ff2-9f84-0f407df86ff1',
            'episode_id': '8da368bd-08d1-46d0-afaa-c134a4af7dc0',
            'description': 'md5:53b5239e4d14973a87125c217c255b2a',
            'duration': 1256.18848,
        },
    }]

    @classmethod
    def _extract_embed_urls(cls, url, webpage):
        for from_ in super(Art19IE, cls)._extract_embed_urls(url, webpage):
            yield from_
        for episode_id in re.findall(
                r'<div\b[^>]+\bclass\s*=\s*[\'"][^\'"]*art19-web-player[^\'"]*[\'"][^>]+\bdata-episode-id=[\'"]({0})[\'"]'.format(cls._UUID_REGEX), webpage):
            yield 'https://rss.art19.com/episodes/{0}.mp3'.format(episode_id)

    def _real_extract(self, url):
        episode_id = self._match_id(url)

        player_metadata = self._download_json(
            'https://art19.com/episodes/{0}'.format(episode_id), episode_id,
            note='Downloading player metadata', fatal=False,
            headers={'Accept': 'application/vnd.art19.v0+json'})
        rss_metadata = self._download_json(
            'https://rss.art19.com/episodes/{0}.json'.format(episode_id), episode_id,
            fatal=False, note='Downloading RSS metadata')

        formats = [{
            'format_id': 'direct',
            'url': 'https://rss.art19.com/episodes/{0}.mp3'.format(episode_id),
            'vcodec': 'none',
            'acodec': 'mp3',
        }]
        for fmt_id, fmt_data in traverse_obj(rss_metadata, (
                'content', 'media', T(dict.items),
                lambda _, k_v: k_v[0] != 'waveform_bin' and k_v[1].get('url'))):
            fmt_url = url_or_none(fmt_data['url'])
            if not fmt_url:
                continue
            formats.append({
                'format_id': fmt_id,
                'url': fmt_url,
                'vcodec': 'none',
                'acodec': fmt_id,
                'quality': -2 if fmt_id == 'ogg' else -1,
            })

        self._sort_formats(formats)

        return merge_dicts({
            'id': episode_id,
            'formats': formats,
        }, traverse_obj(player_metadata, ('episode', {
            'title': ('title', T(str_or_none)),
            'description': ('description_plain', T(str_or_none)),
            'episode_id': ('id', T(str_or_none)),
            'episode_number': ('episode_number', T(int_or_none)),
            'season_id': ('season_id', T(str_or_none)),
            'series_id': ('series_id', T(str_or_none)),
            'timestamp': ('created_at', T(parse_iso8601)),
            'release_timestamp': ('released_at', T(parse_iso8601)),
            'modified_timestamp': ('updated_at', T(parse_iso8601)),
        })), traverse_obj(rss_metadata, ('content', {
            'title': ('episode_title', T(str_or_none)),
            'description': ('episode_description_plain', T(str_or_none)),
            'episode_id': ('episode_id', T(str_or_none)),
            'episode_number': ('episode_number', T(int_or_none)),
            'season': ('season_title', T(str_or_none)),
            'season_id': ('season_id', T(str_or_none)),
            'season_number': ('season_number', T(int_or_none)),
            'series': ('series_title', T(str_or_none)),
            'series_id': ('series_id', T(str_or_none)),
            'thumbnail': ('cover_image', T(url_or_none)),
            'duration': ('duration', T(float_or_none)),
        })), rev=True)


class Art19ShowIE(InfoExtractor):
    IE_DESC = 'Art19 series'
    _VALID_URL_BASE = r'https?://(?:www\.)?art19\.com/shows/(?P<id>[\w-]+)(?:/embed)?/?'
    _VALID_URL = (
        r'{0}(?:$|[#?])'.format(_VALID_URL_BASE),
        r'https?://rss\.art19\.com/(?P<id>[\w-]+)/?(?:$|[#?])',
    )
    _EMBED_REGEX = (r'<iframe[^>]+\bsrc=[\'"](?P<url>{0}[^\'"])'.format(_VALID_URL_BASE),)

    _TESTS = [{
        'url': 'https://www.art19.com/shows/5898c087-a14f-48dc-b6fc-a2280a1ff6e0/',
        'info_dict': {
            '_type': 'playlist',
            'id': '5898c087-a14f-48dc-b6fc-a2280a1ff6e0',
            'display_id': 'echt-gebeurd',
            'title': 'Echt Gebeurd',
            'description': r're:(?us)Bij\sEcht Gebeurd\svertellen mensen .{1166} Eline Veldhuisen\.$',
            'timestamp': 1492642167,
            # 'upload_date': '20170419',
            'modified_timestamp': int,
            # 'modified_date': str,
            'tags': 'count:7',
        },
        'playlist_mincount': 425,
    }, {
        'url': 'https://rss.art19.com/scamfluencers',
        'info_dict': {
            '_type': 'playlist',
            'id': 'd3c9b8ca-26b3-42f4-9bd8-21d1a9031e75',
            'display_id': 'scamfluencers',
            'title': 'Scamfluencers',
            'description': r're:(?s)You never really know someone\b.{1078} wondery\.com/links/scamfluencers/ now\.$',
            'timestamp': 1647368573,
            # 'upload_date': '20220315',
            'modified_timestamp': int,
            # 'modified_date': str,
            'tags': [],
        },
        'playlist_mincount': 90,
    }, {
        'url': 'https://art19.com/shows/enthuellt/embed',
        'info_dict': {
            '_type': 'playlist',
            'id': 'e2cacf57-bb8a-4263-aa81-719bcdd4f80c',
            'display_id': 'enthuellt',
            'title': 'Enthüllt',
            'description': 'md5:17752246643414a2fd51744fc9a1c08e',
            'timestamp': 1601645860,
            # 'upload_date': '20201002',
            'modified_timestamp': int,
            # 'modified_date': str,
            'tags': 'count:10',
        },
        'playlist_mincount': 10,
        'skip': 'Content not found',
    }]
    _WEBPAGE_TESTS = [{
        'url': 'https://deconstructingyourself.com/deconstructing-yourself-podcast',
        'info_dict': {
            '_type': 'playlist',
            'id': 'cfbb9b01-c295-4adb-8726-adde7c03cf21',
            'display_id': 'deconstructing-yourself',
            'title': 'Deconstructing Yourself',
            'description': 'md5:dab5082b28b248a35476abf64768854d',
            'timestamp': 1570581181,
            # 'upload_date': '20191009',
            'modified_timestamp': int,
            # 'modified_date': str,
            'tags': 'count:5',
        },
        'playlist_mincount': 80,
    }, {
        'url': 'https://chicagoreader.com/columns-opinion/podcasts/ben-joravsky-show-podcast-episodes/',
        'info_dict': {
            '_type': 'playlist',
            'id': '9dfa2c37-ab87-4c13-8388-4897914313ec',
            'display_id': 'the-ben-joravsky-show',
            'title': 'The Ben Joravsky Show',
            'description': 'md5:c0f3ec0ee0dbea764390e521adc8780a',
            'timestamp': 1550875095,
            # 'upload_date': '20190222',
            'modified_timestamp': int,
            # 'modified_date': str,
            'tags': ['Chicago Politics', 'chicago', 'Ben Joravsky'],
        },
        'playlist_mincount': 1900,
    }]

    @classmethod
    def _extract_embed_urls(cls, url, webpage):
        for from_ in super(Art19ShowIE, cls)._extract_embed_urls(url, webpage):
            yield from_
        for series_id in re.findall(
                r'<div[^>]+\bclass=[\'"][^\'"]*art19-web-player[^\'"]*[\'"][^>]+\bdata-series-id=[\'"]([\w-]+)[\'"]', webpage):
            yield 'https://art19.com/shows/{0}'.format(series_id)

    def _real_extract(self, url):
        series_id = self._match_id(url)
        for expected in ((403, 404), None):
            series_metadata, urlh = self._download_json_handle(
                'https://art19.com/series/{0}'.format(series_id), series_id, note='Downloading series metadata',
                headers={'Accept': 'application/vnd.art19.v0+json'},
                expected_status=(403, 404))
            if urlh.getcode() == 403:
                # raise the actual problem with the page
                urlh = self._request_webpage(url, series_id, expected_status=404)
                if urlh.getcode() == 404:
                    raise ExtractorError(
                        'content not found, possibly expired',
                        video_id=series_id, expected=True)
            if urlh.getcode() not in (expected or []):
                # apparently OK
                break

        return merge_dicts(
            self.playlist_result((
                self.url_result('https://rss.art19.com/episodes/{0}.mp3'.format(episode_id), Art19IE)
                for episode_id in traverse_obj(series_metadata, ('series', 'episode_ids', Ellipsis, T(str_or_none))))),
            traverse_obj(series_metadata, ('series', {
                'id': ('id', T(str_or_none)),
                'display_id': ('slug', T(str_or_none)),
                'title': ('title', T(str_or_none)),
                'description': ('description_plain', T(str_or_none)),
                'timestamp': ('created_at', T(parse_iso8601)),
                'modified_timestamp': ('updated_at', T(parse_iso8601)),
            })),
            traverse_obj(series_metadata, {
                'tags': ('tags', Ellipsis, 'name', T(str_or_none)),
            }, {'tags': T(lambda _: [])}))
