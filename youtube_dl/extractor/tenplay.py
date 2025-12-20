# coding: utf-8
from __future__ import unicode_literals

import functools

from .common import InfoExtractor
from ..compat import (
    compat_itertools_count,
    compat_kwargs,
)
from ..utils import (
    get_elements_by_attribute,
    HEADRequest,
    float_or_none,
    int_or_none,
    merge_dicts,
    NO_DEFAULT,
    T,
    traverse_obj,
    txt_or_none,
    url_or_none,
    urljoin,
)


class TenPlayBase(InfoExtractor):
    _GEO_COUNTRIES = ['AU']
    _GEO_BYPASS = False

    def raise_geo_restricted(self, *args, **kwargs):
        countries = args[1] if len(args) > 1 else kwargs.get('countries', NO_DEFAULT)
        if countries is NO_DEFAULT:
            kwargs['countries'] = self._GEO_COUNTRIES
            kwargs = compat_kwargs(kwargs)
        super(TenPlayBase, self).raise_geo_restricted(*args, **kwargs)

    def _download_webpage_handle(self, url_or_request, video_id, *args, **kwargs):
        res = super(TenPlayBase, self)._download_webpage_handle(url_or_request, video_id, *args, **kwargs)
        if res and any('Sorry, 10 play is not available in your region.' in e
                       for e in get_elements_by_attribute('class', 'iserror__text', res[0])):
            self.raise_geo_restricted()
        return res


class TenPlayIE(TenPlayBase):
    _VALID_URL = r'https?://(?:www\.)?10play\.com\.au/(?:[^/]+/)+(?P<id>tpv\d{6}[a-z]{5})'
    _NETRC_MACHINE = '10play'
    _TESTS = [{
        'url': 'https://10play.com.au/neighbours/web-extras/season-41/heres-a-first-look-at-mischa-bartons-neighbours-debut/tpv230911hyxnz',
        'info_dict': {
            'id': '6336940246112',
            'ext': 'mp4',
            'title': 'Here\'s A First Look At Mischa Barton\'s Neighbours Debut',
            'alt_title': 'Here\'s A First Look At Mischa Barton\'s Neighbours Debut',
            'description': 'Neighbours Premieres Monday, September 18 At 4:30pm On 10 And 10 Play And 6:30pm On 10 Peach',
            'duration': 74,
            'season': 'Season 41',
            'season_number': 41,
            'series': 'Neighbours',
            'thumbnail': r're:https://.*\.jpg',
            'uploader': 'Channel 10',
            'age_limit': 15,
            'timestamp': 1694386800,
            'upload_date': '20230910',
            'uploader_id': '2199827728001',
        },
        'params': {
            'skip_download': True,
        },
        'skip': 'Only available in Australia',
    }, {
        'url': 'https://10play.com.au/neighbours/episodes/season-42/episode-9107/tpv240902nzqyp',
        'info_dict': {
            'id': '9000000000091177',
            'ext': 'mp4',
            'title': 'Neighbours - S42 Ep. 9107',
            'alt_title': 'Thu 05 Sep',
            'description': 'md5:37a1f4271be34b9ee2b533426a5fbaef',
            'duration': 1388,
            'episode': 'Episode 9107',
            'episode_number': 9107,
            'season': 'Season 42',
            'season_number': 42,
            'series': 'Neighbours',
            'thumbnail': r're:https://.*\.jpg',
            'age_limit': 15,
            'timestamp': 1725517860,
            'upload_date': '20240905',
            'uploader': 'Channel 10',
            'uploader_id': '2199827728001',
        },
        'params': {
            'skip_download': True,
        },
        'skip': 'Only available in Australia',
    }, {
        'url': 'https://10play.com.au/how-to-stay-married/web-extras/season-1/terrys-talks-ep-1-embracing-change/tpv190915ylupc',
        'only_matching': True,
    }]

    _AUS_AGES = {
        'G': 0,
        'PG': 15,
        'M': 15,
        'MA': 15,
        'MA15+': 15,
        'R': 18,
        'X': 18,
    }

    def _real_extract(self, url):
        content_id = self._match_id(url)
        data = self._download_json(
            'https://10play.com.au/api/v1/videos/' + content_id, content_id)

        video_data = self._download_json(
            'https://vod.ten.com.au/api/videos/bcquery?command=find_videos_by_id&video_id={0}'.format(data['altId']),
            content_id, 'Downloading video JSON')
        m3u8_url = self._request_webpage(
            HEADRequest(video_data['items'][0]['HLSURL']),
            content_id, 'Checking stream URL').url
        if '10play-not-in-oz' in m3u8_url:
            self.raise_geo_restricted()
        # Attempt to get a higher quality stream
        m3u8_url = m3u8_url.replace(',150,75,55,0000', ',300,150,75,55,0000')
        formats = self._extract_m3u8_formats(m3u8_url, content_id, 'mp4')
        self._sort_formats(formats)

        return merge_dicts({
            'id': content_id,
            'formats': formats,
            'uploader': 'Channel 10',
            'uploader_id': '2199827728001',
        }, traverse_obj(data, {
            'subtitles': ('captionUrl', T(lambda x: None if x is None
                                          else {'en': [{'url': x}]})),
            'id': ('altId', T(txt_or_none)),
            'duration': ('duration', T(float_or_none)),
            'title': ('subtitle', T(txt_or_none)),
            'alt_title': ('title', T(txt_or_none)),
            'description': ('description', T(txt_or_none)),
            'age_limit': ('classification', T(self._AUS_AGES.get)),
            'series': ('tvShow', T(txt_or_none)),
            'season_number': ('season', T(int_or_none)),
            'episode_number': ('episode', T(int_or_none)),
            'timestamp': ('published', T(int_or_none)),
            'thumbnail': ('imageUrl', T(url_or_none)),
        }), rev=True)


class TenPlaySeasonIE(TenPlayBase):
    _VALID_URL = r'https?://(?:www\.)?10play\.com\.au/(?P<show>[^/?#]+)/episodes/(?P<season>[^/?#]+)/?(?:$|[?#])'
    _TESTS = [{
        'url': 'https://10play.com.au/masterchef/episodes/season-14',
        'info_dict': {
            'title': 'Season 14',
            'id': 'MjMyOTIy',
        },
        'playlist_mincount': 64,
        'skip': 'Only available in Australia',
    }, {
        'url': 'https://10play.com.au/the-bold-and-the-beautiful-fast-tracked/episodes/season-2022',
        'info_dict': {
            'title': 'Season 2022',
            'id': 'Mjc0OTIw',
        },
        'playlist_mincount': 256,
        'skip': 'Only available in Australia',
    }]

    def _entries(self, load_more_url, display_id=None):
        skip_ids = []
        for page in compat_itertools_count(1):
            episodes_carousel = self._download_json(
                load_more_url, display_id, query={'skipIds[]': skip_ids},
                note='Fetching episodes page {0}'.format(page))

            episodes_chunk = episodes_carousel['items']
            skip_ids.extend(ep['id'] for ep in episodes_chunk)

            for ep in episodes_chunk:
                yield ep['cardLink']
            if not episodes_carousel.get('hasMore'):
                break

    def _real_extract(self, url):
        show, season = self._match_valid_url(url).group('show', 'season')
        season_info = self._download_json(*(s.format(show=show, season=season) for s in (
            'https://10play.com.au/api/shows/{show}/episodes/{season}', '{show}/{season}')
        ))

        episodes_carousel = traverse_obj(season_info, (
            'content', 0, 'components', (
                lambda _, v: v['title'].lower() == 'episodes',
                (Ellipsis, T(dict)),
            )), any) or {}

        playlist_id = episodes_carousel['tpId']

        return self.playlist_from_matches(
            self._entries(urljoin(url, episodes_carousel['loadMoreUrl']), playlist_id),
            playlist_id, traverse_obj(season_info, ('content', 0, 'title', T(txt_or_none))),
            getter=functools.partial(urljoin, url))
